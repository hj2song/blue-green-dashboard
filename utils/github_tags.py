import requests
from datetime import datetime
import re

def get_repository_tags(username, token, owner, repo, limit=50):
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"token {token}"
    }
    
    # 한 번에 최대 100개의 태그를 가져오도록 설정 (필터링 후 충분한 결과를 얻기 위해)
    tags_url = f"https://api.github.com/repos/{owner}/{repo}/tags?per_page=100"
    
    try:
        # 단일 API 호출로 태그 정보 가져오기
        response = requests.get(tags_url, headers=headers)
        response.raise_for_status()
        
        tags = response.json()
        print(f"받은 태그 수: {len(tags)}")
        
        # 패턴에 맞는 태그만 필터링
        # 예시 패턴: "2025/w13/master-20250324_v01"
        pattern = r'\d{4}/w\d+/master-\d{8}_v\d+'
        
        filtered_tags = []
        for tag in tags:
            tag_name = tag['name']
            # 정규 표현식 패턴과 일치하는 태그만 포함
            if re.match(pattern, tag_name):
                commit_sha = tag['commit']['sha']
                
                # 태그 이름에서 날짜 추출
                date_str = 'Unknown'
                date_match = re.search(r'(\d{8})_v\d+', tag_name)
                if date_match:
                    date_str_raw = date_match.group(1)
                    try:
                        # 20250324 형식을 2025-03-24 형식으로 변환
                        d = datetime.strptime(date_str_raw, '%Y%m%d')
                        date_str = d.strftime('%Y-%m-%d')
                    except:
                        pass
                
                filtered_tags.append({
                    'name': tag_name,
                    'date': date_str,
                    'commit_sha': commit_sha[:7],
                    'commit_url': f"https://github.com/{owner}/{repo}/commit/{commit_sha}"
                })
        
        # 태그 이름으로 정렬 (최신순)
        filtered_tags.sort(key=lambda x: x['name'], reverse=True)
        
        # 최대 limit 개수만큼 반환
        return filtered_tags[:limit]
        
    except requests.exceptions.RequestException as e:
        print(f"GitHub API 요청 중 오류 발생: {str(e)}")
        if hasattr(e, 'response') and e.response:
            print(f"응답 상태 코드: {e.response.status_code}")
            print(f"응답 내용: {e.response.text}")
        raise Exception(f"GitHub API 요청 오류: {str(e)}")

def get_multiple_repos_tags(username, token, repos, limit=50):
    all_tags = {}
    
    for repo_info in repos:
        owner = repo_info['owner']
        repo = repo_info['repo']
        repo_key = f"{owner}/{repo}"
        
        try:
            print(f"레포지토리 태그 조회 시작: {repo_key}")
            tags = get_repository_tags(username, token, owner, repo, limit)
            all_tags[repo_key] = tags
            print(f"레포지토리 태그 조회 완료: {repo_key}, {len(tags)}개 필터링된 태그")
        except Exception as e:
            print(f"레포지토리 {repo_key} 태그 조회 실패: {str(e)}")
            all_tags[repo_key] = []
    
    return all_tags