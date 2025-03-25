import requests
from datetime import datetime

def get_repository_tags(username, token, owner, repo, limit=50):
    """
    GitHub API를 사용하여 지정된 레포지토리의 태그 목록을 가져옵니다.
    
    Args:
        username (str): GitHub 사용자명
        token (str): GitHub 액세스 토큰
        owner (str): 레포지토리 소유자 (organization 또는 사용자)
        repo (str): 레포지토리 이름
        limit (int, optional): 가져올 태그의 최대 수. 기본값은 50.
        
    Returns:
        list: 태그 정보 딕셔너리의 리스트. 각 딕셔너리는 태그명, 날짜, 커밋 SHA 등을 포함합니다.
    """
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"token {token}"
    }
    
    tags_url = f"https://api.github.com/repos/{owner}/{repo}/tags"
    tags_data = []
    
    try:
        response = requests.get(tags_url, headers=headers)
        response.raise_for_status()  # HTTP 오류 발생시 예외 발생
        
        tags = response.json()
        
        # 각 태그에 대한 커밋 정보 가져오기 (날짜 정보 포함)
        for tag in tags[:limit]:  # 지정된 수만큼만 처리
            tag_name = tag['name']
            commit_sha = tag['commit']['sha']
            
            # 커밋 정보 가져오기
            commit_url = f"https://api.github.com/repos/{owner}/{repo}/commits/{commit_sha}"
            commit_response = requests.get(commit_url, headers=headers)
            commit_response.raise_for_status()
            
            commit_data = commit_response.json()
            commit_date = commit_data['commit']['committer']['date']
            
            # 날짜를 사람이 읽기 쉬운 형식으로 변환
            formatted_date = datetime.fromisoformat(commit_date.replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M:%S')
            
            tags_data.append({
                'name': tag_name,
                'date': formatted_date,
                'commit_sha': commit_sha[:7],  # 짧은 SHA 해시
                'commit_url': commit_data['html_url']
            })
        
        # 날짜를 기준으로 최신순 정렬
        tags_data.sort(key=lambda x: datetime.strptime(x['date'], '%Y-%m-%d %H:%M:%S'), reverse=True)
        
        return tags_data
        
    except requests.exceptions.RequestException as e:
        print(f"GitHub API 요청 중 오류 발생: {str(e)}")
        return []

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
        
        tags = get_repository_tags(username, token, owner, repo, limit)
        all_tags[repo_key] = tags
    
    return all_tags
