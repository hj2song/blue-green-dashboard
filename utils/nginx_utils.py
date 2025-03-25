import os
import subprocess
import re

# 원격 서버 연결 정보
REMOTE_HOST = '222.239.193.163'
REMOTE_PORT = '6304'
REMOTE_USER = 'linux'
REMOTE_PASS = 'gbnet2014!'  # 테스트 목적으로만 사용

def run_remote_command(command):
    """원격 서버에서 명령어를 실행하고 결과를 반환합니다."""
    try:
        ssh_command = f"sshpass -p '{REMOTE_PASS}' ssh -p {REMOTE_PORT} -o StrictHostKeyChecking=no {REMOTE_USER}@{REMOTE_HOST} '{command}'"
        result = subprocess.run(ssh_command, shell=True, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return result.stdout.strip()
    except Exception as e:
        print(f"원격 명령어 실행 중 오류: {e}")
        return ""

def parse_nginx_conf(app, env):
    """원격 서버의 Nginx 설정을 파싱하여 블루/그린 서비스 정보를 추출합니다."""
    conf_path = f"/etc/nginx/conf.d/{app}.conf"
    
    # 원격 서버에서 파일 존재 확인
    file_check = run_remote_command(f"sudo test -f {conf_path} && echo 'EXISTS' || echo 'NOT_EXISTS'")
    if file_check != "EXISTS":
        print(f"Config file not found: {conf_path}")
        return "unknown", "unknown"
    
    try:
        config_name = f"{app}"
        
        # 먼저 설정 파일의 주석에서 직접 정보 찾기 시도
        file_content = run_remote_command(f"sudo cat {conf_path}")
        
        # 주석에서 색상 정보 찾기 (더 신뢰할 수 있는 방법)
        main_comment_match = re.search(r'#\s*실제\s*서비스:\s*(\w+)', file_content)
        test_comment_match = re.search(r'#\s*테스트\s*서비스:\s*(\w+)', file_content)
        
        if main_comment_match and test_comment_match:
            main_service = main_comment_match.group(1)
            test_service = test_comment_match.group(1)
            print(f"주석에서 서비스 정보 찾음: main={main_service}, test={test_service}")
            return main_service, test_service
            
        # 테스트 서비스 색상 추출 (head -n1)
        test_service_cmd = (
            f"sudo nginx -T 2>/dev/null | "
            f"grep -A 100 {config_name}.conf | "
            f"grep proxy_pass | "
            f"head -n1"
        )
        test_service_line = run_remote_command(test_service_cmd).strip()
        print(f"Test service cmd result for {app} ({env}): '{test_service_line}'")
        
        # 실제 서비스 색상 추출 (tail -n1)
        main_service_cmd = (
            f"sudo nginx -T 2>/dev/null | "
            f"grep -A 100 {config_name}.conf | "
            f"grep proxy_pass | "
            f"tail -n1"
        )
        main_service_line = run_remote_command(main_service_cmd).strip()
        print(f"Main service cmd result for {app} ({env}): '{main_service_line}'")
        
        # 서버 이름에서 색상 추출 (다양한 패턴 지원)
        # office_servers_blue 또는 xxx-blue_meatbox 형식 모두 처리
        def extract_color(line):
            # 서버 이름 추출
            server_match = re.search(r'http://([^;/\s]+)', line)
            if not server_match:
                return None
                
            server_name = server_match.group(1)
            print(f"서버 이름: {server_name}")
            
            # 색상 추출 시도 (여러 패턴)
            # 패턴 1: servers_blue 형식
            color_match1 = re.search(r'servers?_([a-z]+)$', server_name)
            if color_match1:
                return color_match1.group(1)
                
            # 패턴 2: -blue_meatbox 형식
            color_match2 = re.search(r'-([a-z]+)_', server_name)
            if color_match2:
                return color_match2.group(1)
                
            # 패턴 3: _blue 형식 (끝에 위치)
            color_match3 = re.search(r'_([a-z]+)$', server_name)
            if color_match3:
                return color_match3.group(1)
                
            # 패턴 4: blue가 포함된 경우 (덜 정확함)
            if 'blue' in server_name.lower():
                return 'blue'
            if 'green' in server_name.lower():
                return 'green'
                
            return None
        
        # 색상 추출
        test_service = extract_color(test_service_line)
        main_service = extract_color(main_service_line)
        
        print(f"추출된 색상: main={main_service}, test={test_service}")
        
        return main_service or "unknown", test_service or "unknown"
    except Exception as e:
        print(f"Error parsing nginx config for {env}-{app}: {e}")
        return "unknown", "unknown"

# 테스트용 코드
if __name__ == "__main__":
    app = "office"
    env = "prod"
    main, test = parse_nginx_conf(app, env)
    print(f"최종 결과: main={main}, test={test}")
