from flask import Flask, render_template, request, redirect, url_for, jsonify, session
from datetime import datetime
import os
import json
import requests
from utils.docker_utils import get_service_info
from utils.nginx_utils import parse_nginx_conf
from utils.github_tags import get_multiple_repos_tags  # 새로 추가된 GitHub 태그 관련 모듈

# 정적 파일 경로 변경
app = Flask(__name__, static_folder='static', static_url_path='/static')
app.secret_key = os.urandom(24)  # 세션 사용을 위한 secret key 설정

# config.json 파일에서 설정 로드
def load_config():
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # 기본 설정값
        return {
            "environments": ["prod"],
            "applications": ["admin", "office", "docs", "web", "mobile"],
            "default_refresh_interval": 10,
            "github_owner": "meatbox-git",
            "github_repo": "meatbox-docker"
        }

# 글로벌 설정 변수
config = load_config()
ENVIRONMENTS = config.get("environments", ["prod"])
APPLICATIONS = config.get("applications", ["admin", "office", "docs", "web", "mobile"])
DEFAULT_REFRESH_INTERVAL = config.get("default_refresh_interval", 10)
GITHUB_OWNER = config.get("github_owner", "")  # 기본 값 제거
GITHUB_REPO = config.get("github_repo", "meatbox-docker")

def get_app_services_info(selected_app=None):
    """선택된 앱 또는 모든 앱의 서비스 정보를 수집합니다."""
    services_info = []
    for env in ENVIRONMENTS:
        # 선택된 앱이 있으면 해당 앱만 처리, 없으면 모든 앱 처리
        apps_to_process = [selected_app] if selected_app in APPLICATIONS else []
        for app in apps_to_process:
            main_service, test_service = parse_nginx_conf(app, env)
            for color in ["blue", "green"]:
                service_name = f"{env}-{app}-{color}_meatbox"
                replicas, image_tag, port_forwarding = get_service_info(service_name)
                if replicas:  # 서비스가 존재하는 경우만 추가
                    if color == main_service:
                        service_status = "서비스중"
                    elif color == test_service:
                        service_status = "테스트중"
                    else:
                        service_status = "비활성"
                    services_info.append({
                        "env": env,
                        "app": app,
                        "color": color,
                        "name": service_name,
                        "status": service_status,
                        "replicas": replicas,
                        "image_tag": image_tag,
                        "port_forwarding": port_forwarding
                    })
    return services_info

@app.route('/')
def index():
    """앱 선택 페이지를 렌더링합니다."""
    # 세션에서 새로고침 설정 가져오기 (없으면 기본값 설정)
    if 'refresh_enabled' not in session:
        session['refresh_enabled'] = True
    if 'refresh_interval' not in session:
        session['refresh_interval'] = DEFAULT_REFRESH_INTERVAL
    # GitHub 계정 및 토큰 상태 확인
    has_github_info = 'github_username' in session and session['github_username'] and 'github_token' in session and session['github_token']
    return render_template('app_selector.html',
                          applications=APPLICATIONS,
                          refresh_enabled=session['refresh_enabled'],
                          refresh_interval=session['refresh_interval'],
                          has_github_info=has_github_info,
                          github_username=session.get('github_username', ''))

@app.route('/dashboard/<app_name>')
def dashboard(app_name):
    """선택된 앱에 대한 대시보드를 렌더링합니다."""
    if app_name not in APPLICATIONS:
        return redirect(url_for('index'))
    # 세션에서 새로고침 설정 가져오기 (없으면 기본값 설정)
    if 'refresh_enabled' not in session:
        session['refresh_enabled'] = True
    if 'refresh_interval' not in session:
        session['refresh_interval'] = DEFAULT_REFRESH_INTERVAL
    # GitHub 계정 및 토큰 상태 확인
    has_github_info = 'github_username' in session and session['github_username'] and 'github_token' in session and session['github_token']
    # 이전에 보던 앱 정보를 세션에서 가져옴
    previous_app = session.get('current_app', None)
    # 앱이 변경되었거나 자동 새로고침이 활성화된 경우 데이터를 새로 가져옴
    if app_name != previous_app or session['refresh_enabled']:
        services_info = get_app_services_info(app_name)
        # 현재 보고 있는 앱 정보를 세션에 저장
        session['current_app'] = app_name
        # 데이터를 세션에 저장
        session['services_info'] = services_info
    else:
        # 같은 앱이고 자동 새로고침이 비활성화된 경우 이전 데이터 재사용
        services_info = session.get('services_info', [])
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return render_template('index.html',
                          services=services_info,
                          timestamp=timestamp,
                          selected_app=app_name,
                          applications=APPLICATIONS,
                          refresh_enabled=session['refresh_enabled'],
                          refresh_interval=session['refresh_interval'],
                          has_github_info=has_github_info,
                          github_username=session.get('github_username', ''))

@app.route('/api/refresh', methods=['POST'])
def update_refresh():
    """새로고침 설정을 업데이트합니다."""
    data = request.json
    
    # 변경 사항을 감지하기 위해 이전 상태 저장
    previous_enabled = session.get('refresh_enabled', True)
    
    if 'enabled' in data:
        session['refresh_enabled'] = data['enabled']
        print(f"Refresh enabled updated: {session['refresh_enabled']}")
    
    if 'interval' in data:
        session['refresh_interval'] = int(data['interval'])  # 정수로 변환
        print(f"Refresh interval updated: {session['refresh_interval']}")
    
    session.modified = True  # 세션 변경 사항 저장
    
    # 클라이언트에 유용할 수 있는 추가 정보 반환
    return jsonify({
        "status": "success", 
        "previous_enabled": previous_enabled,
        "current_enabled": session['refresh_enabled'],
        "interval": session['refresh_interval']
    })

@app.route('/api/github/info', methods=['POST'])
def update_github_info():
    """GitHub 계정과 토큰 정보를 업데이트합니다."""
    data = request.json
    if 'username' in data and 'token' in data:
        # 토큰 검증을 위해 간단한 GitHub API 요청 수행
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f"token {data['token']}"
        }
        try:
            # GitHub API로 토큰 유효성 검사 (간단한 사용자 정보 조회)
            response = requests.get("https://api.github.com/user", headers=headers)
            if response.status_code == 200:
                session['github_username'] = data['username']
                session['github_token'] = data['token']
                session.modified = True
                return jsonify({"status": "success", "message": "GitHub 계정 정보가 저장되었습니다."})
            else:
                return jsonify({"status": "error", "message": "유효하지 않은 토큰입니다."})
        except Exception as e:
            return jsonify({"status": "error", "message": f"GitHub 정보 검증 중 오류 발생: {str(e)}"})
    return jsonify({"status": "error", "message": "GitHub 계정 또는 토큰이 제공되지 않았습니다."})

@app.route('/api/github/info/remove', methods=['POST'])
def remove_github_info():
    """GitHub 계정과 토큰 정보를 세션에서 제거합니다."""
    if 'github_username' in session:
        session.pop('github_username')
    if 'github_token' in session:
        session.pop('github_token')
    session.modified = True
    return jsonify({"status": "success", "message": "GitHub 계정 정보가 제거되었습니다."})

@app.route('/api/github/info/status', methods=['GET'])
def github_info_status():
    """GitHub 계정과 토큰 정보의 상태를 반환합니다."""
    has_github_info = 'github_username' in session and session['github_username'] and 'github_token' in session and session['github_token']
    username = session.get('github_username', '') if has_github_info else ''
    return jsonify({
        "status": "success", 
        "has_github_info": has_github_info,
        "username": username
    })

# 새로 추가: GitHub 태그 정보를 가져오는 API 엔드포인트
@app.route('/api/github/tags', methods=['GET'])
def get_github_tags():
    """GitHub 레포지토리의 태그 정보를 가져옵니다."""
    # 세션에서 GitHub 계정 정보 가져오기
    github_username = session.get('github_username')
    github_token = session.get('github_token')
    
    if not github_username or not github_token:
        return jsonify({
            "status": "error", 
            "message": "GitHub 계정 정보가 설정되지 않았습니다. 먼저 계정 정보를 설정해주세요."
        })
    
    # 태그를 가져올 레포지토리 목록 설정
    repos = [
        {"owner": "meatbox-git", "repo": "meatbox-admin"},
        {"owner": "meatbox-git", "repo": "meatbox-web"}
    ]
    
    try:
        # 여러 레포지토리의 태그 가져오기
        tags_data = get_multiple_repos_tags(github_username, github_token, repos, limit=50)
        return jsonify({"status": "success", "data": tags_data})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/api/github/deploy', methods=['POST'])
def github_deploy():
    """GitHub Actions 워크플로우를 실행하여 컨테이너를 배포합니다."""
    data = request.json
    app = data.get('app')
    env = data.get('env')
    tag = data.get('tag')
    if not all([app, env, tag]):
        return jsonify({"status": "error", "message": "필수 파라미터가 누락되었습니다."})
    
    # 세션에서 GitHub 계정 정보 가져오기
    github_username = session.get('github_username')
    github_token = session.get('github_token')
    
    if not github_username or not github_token:
        return jsonify({"status": "error", "message": "GitHub 계정 정보가 설정되지 않았습니다. 먼저 계정 정보를 설정해주세요."})
    
    # GitHub Actions 워크플로우 실행 API 호출
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"token {github_token}"
    }
    workflow_url = f"https://api.github.com/repos/meatbox-git/{GITHUB_REPO}/actions/workflows/deploy-blue-green.yml/dispatches"
    payload = {
        "ref": "master",  # 워크플로우를 실행할 브랜치
        "inputs": {
            "APP": app,
            "ENV": env,
            "TAG": tag
        }
    }
    try:
        response = requests.post(workflow_url, headers=headers, json=payload)
        if response.status_code in [204, 200]:
            return jsonify({"status": "success"})
        else:
            return jsonify({
                "status": "error", 
                "message": f"GitHub API 응답 오류: {response.status_code}",
                "details": response.text
            })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/api/github/interchange', methods=['POST'])
def github_interchange():
    """GitHub Actions 워크플로우를 실행하여 서비스를 교체합니다."""
    data = request.json
    app = data.get('app')
    env = data.get('env')
    if not all([app, env]):
        return jsonify({"status": "error", "message": "필수 파라미터가 누락되었습니다."})
    
    # 세션에서 GitHub 계정 정보 가져오기
    github_username = session.get('github_username')
    github_token = session.get('github_token')
    
    if not github_username or not github_token:
        return jsonify({"status": "error", "message": "GitHub 계정 정보가 설정되지 않았습니다. 먼저 계정 정보를 설정해주세요."})
    
    # GitHub Actions 워크플로우 실행 API 호출
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"token {github_token}"
    }
    workflow_url = f"https://api.github.com/repos/meatbox-git/{GITHUB_REPO}/actions/workflows/interchange-blue-green.yml/dispatches"
    payload = {
        "ref": "master",  # 워크플로우를 실행할 브랜치
        "inputs": {
            "APP": app,
            "ENV": env
        }
    }
    try:
        response = requests.post(workflow_url, headers=headers, json=payload)
        if response.status_code in [204, 200]:
            return jsonify({"status": "success"})
        else:
            return jsonify({
                "status": "error", 
                "message": f"GitHub API 응답 오류: {response.status_code}",
                "details": response.text
            })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/api/manual_refresh/<app_name>', methods=['GET'])
def manual_refresh(app_name):
    """수동 새로고침을 처리합니다."""
    if app_name not in APPLICATIONS:
        return jsonify({"status": "error", "message": "잘못된 앱 이름입니다."})
    # 자동 새로고침 설정에 관계없이 항상 최신 데이터를 가져옴
    services_info = get_app_services_info(app_name)
    session['services_info'] = services_info
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return jsonify({
        "status": "success",
        "services": services_info,
        "timestamp": timestamp
    })

@app.route('/api/github/info/direct', methods=['POST'])
def set_github_info_direct():
    """폼에서 직접 제출된 GitHub 계정 정보를 처리합니다."""
    username = request.form.get('github_username')
    token = request.form.get('github_token')
    
    if not username or not token:
        return redirect(url_for('index'))
    
    # 토큰 검증을 위해 간단한 GitHub API 요청 수행
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"token {token}"
    }
    try:
        # GitHub API로 토큰 유효성 검사 (간단한 사용자 정보 조회)
        response = requests.get("https://api.github.com/user", headers=headers)
        if response.status_code == 200:
            session['github_username'] = username
            session['github_token'] = token
            session.modified = True
            # 성공 메시지를 플래시 메시지로 추가할 수도 있습니다
        else:
            # 실패 메시지를 플래시 메시지로 추가할 수도 있습니다
            pass
    except Exception as e:
        print(f"GitHub 계정 정보 검증 중 오류 발생: {str(e)}")
    
    # 원래 페이지로 리디렉션
    referrer = request.referrer
    if referrer:
        return redirect(referrer)
    return redirect(url_for('index'))

if __name__ == "__main__":
    from waitress import serve
    print("블루-그린 배포 상태 대시보드 서버가 시작되었습니다.")
    serve(app, host="0.0.0.0", port=38080)
