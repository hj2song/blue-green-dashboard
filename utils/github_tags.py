import requests
from datetime import datetime

def get_repository_tags(username, token, owner, repo, limit=50):
    """
    GitHub API를 사용하여 지정된 레포지토리의 태그 목록을 가져옵니다.
    간소화 버전: 태그 이름과 커밋 SHA만 빠르게 가져옵니다.
    
    Args:
        username (str): GitHub 사용자명
        token (str): GitHub 액세스 토큰
        owner (str): 레포지토리 소유자 (organization 또는 사용자)
        repo (str): 레포지토리 이름
        limit (int, optional): 가져올 태그의 최대 수. 기본값은 50.
        
    Returns:
        list: 태그 정보 딕셔너리의 리스트. 각 딕셔너리는 태그명, 커밋 SHA를 포함합니다.
    """
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"token {token}"
    }
    
    # 태그 목록만 한 번에 가져옵니다
    tags_url = f"https://api.github.com/repos/{owner}/{repo}/tags?per_page={limit}"
    
    try:
        # 단일 API 호출로 태그 정보 가져오기
        response = requests.get(tags_url, headers=headers)
        response.raise_for_status()
        
        tags = response.json()
        print(f"받은 태그 수: {len(tags)}")
        
        # 중요 정보만 추출
        tags_data = []
        for tag in tags[:limit]:
            tag_name = tag['name']
            commit_sha = tag['commit']['sha']
            
            # 태그 생성 날짜 추정 (태그 이름에서 추출)
            date_str = 'Unknown'
            # 태그 이름에서 날짜 추출 시도 (예: 2025/w13/master-20250324_v01)
            date_match = None
            import re
            date_match = re.search(r'(\d{8})_v\d+', tag_name)
            if date_match:
                date_str_raw = date_match.group(1)
                try:
                    # 20250324 형식을 2025-03-24 형식으로 변환
                    d = datetime.strptime(date_str_raw, '%Y%m%d')
                    date_str = d.strftime('%Y-%m-%d')
                except:
                    pass
            
            tags_data.append({
                'name': tag_name,
                'date': date_str,
                'commit_sha': commit_sha[:7],
                'commit_url': f"https://github.com/{owner}/{repo}/commit/{commit_sha}"
            })
        
        # 태그 이름으로 정렬 (최신 태그가 상단에 오도록)
        tags_data.sort(key=lambda x: x['name'], reverse=True)
        
        return tags_data
        
    except requests.exceptions.RequestException as e:
        print(f"GitHub API 요청 중 오류 발생: {str(e)}")
        if hasattr(e, 'response') and e.response:
            print(f"응답 상태 코드: {e.response.status_code}")
            print(f"응답 내용: {e.response.text}")
        raise Exception(f"GitHub API 요청 오류: {str(e)}")

def get_multiple_repos_tags(username, token, repos, limit=30):
    """
    여러 저장소의 태그를 가져와 통합한 목록을 반환합니다.
    
    Args:
        username (str): GitHub 사용자명
        token (str): GitHub 액세스 토큰
        repos (list): 레포지토리 정보 딕셔너리의 리스트. 각 딕셔너리는 'owner'와 'repo' 키를 포함해야 함.
        limit (int, optional): 각 레포지토리에서 가져올 태그의 최대 수. 기본값은 30.
        
    Returns:
        dict: 레포지토리별 태그 정보
    """
    all_tags = {}
    
    for repo_info in repos:
        owner = repo_info['owner']
        repo = repo_info['repo']
        repo_key = f"{owner}/{repo}"
        
        try:
            print(f"레포지토리 태그 조회 시작: {repo_key}")
            tags = get_repository_tags(username, token, owner, repo, limit)
            all_tags[repo_key] = tags
            print(f"레포지토리 태그 조회 완료: {repo_key}, {len(tags)}개 태그")
        except Exception as e:
            print(f"레포지토리 {repo_key} 태그 조회 실패: {str(e)}")
            all_tags[repo_key] = []
    
    return all_tags