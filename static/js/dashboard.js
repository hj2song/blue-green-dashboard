(function() {
    // Keep track of whether event handlers have been initialized
    let initialized = false;
    
    // 태그 데이터 저장 변수
    let tagsData = null;
    let selectedRepo = null;
    let selectedTag = null;

    // Function to initialize all event handlers
    function initEventHandlers() {
        // Don't initialize more than once
        if (initialized) return;
        
        // Flag that we've initialized
        initialized = true;
        
        // Reference all needed DOM elements
        const refreshToggle = document.getElementById('refresh-toggle');
        const refreshInterval = document.getElementById('refresh-interval');
        const customIntervalContainer = document.getElementById('custom-interval-container');
        const customIntervalValue = document.getElementById('custom-interval-value');
        const manualRefreshButton = document.getElementById('manual-refresh');
        const deployButton = document.getElementById('deploy-button');
        const interchangeButton = document.getElementById('interchange-button');
        const tagsButton = document.getElementById('tags-button'); // 새로 추가
        const removeGithubInfoButton = document.getElementById('remove-github-info-button');
        const deployModal = document.getElementById('deploy-modal');
        const interchangeModal = document.getElementById('interchange-modal');
        const tagsModal = document.getElementById('tags-modal'); // 새로 추가
        const closeButtons = document.querySelectorAll('.close-modal, .cancel-button');
        const deploySubmit = document.getElementById('deploy-submit');
        const interchangeSubmit = document.getElementById('interchange-submit');
        const copySelectedTag = document.getElementById('copy-selected-tag'); // 새로 추가
        const githubInfoForm = document.getElementById('github-info-form');
        const githubInputs = document.querySelectorAll('#github-username-input, #github-token-input');
        const refreshMeta = document.getElementById('refresh-meta');
        const originalRefreshContent = refreshMeta ? refreshMeta.getAttribute('content') : null;

        console.log('Initialize event handlers - Dashboard JS loaded once');

        // GitHub 입력 필드에 포커스될 때 새로고침 일시 중지
        githubInputs.forEach(input => {
            if (!input) return;
            
            input.addEventListener('focus', function() {
                if (refreshMeta) {
                    // 새로고침 일시 중지를 위해 매우 큰 값으로 설정
                    refreshMeta.setAttribute('content', '999999');
                }
            });
            
            // 포커스가 해제될 때 (입력 완료 시) 새로고침 복원 (자동 새로고침이 활성화된 경우에만)
            input.addEventListener('blur', function() {
                if (refreshMeta && refreshToggle && refreshToggle.checked && originalRefreshContent) {
                    // 원래 설정된 새로고침 간격으로 복원
                    refreshMeta.setAttribute('content', originalRefreshContent);
                }
            });
        });

        // 모달 닫기 버튼 이벤트 핸들러
        closeButtons.forEach(button => {
            if (!button) return;
            
            button.addEventListener('click', function() {
                const modalId = this.getAttribute('data-modal');
                if (modalId && document.getElementById(modalId)) {
                    document.getElementById(modalId).style.display = 'none';
                }
            });
        });

        // 모달 열기 이벤트 핸들러
        if (deployButton) {
            deployButton.addEventListener('click', function() {
                if (deployModal) {
                    deployModal.style.display = 'block';
                }
            });
        }
        
        if (interchangeButton) {
            interchangeButton.addEventListener('click', function() {
                if (interchangeModal) {
                    interchangeModal.style.display = 'block';
                }
            });
        }

        // 태그 확인 버튼 이벤트 핸들러
        if (tagsButton) {
            tagsButton.addEventListener('click', function() {
                console.log('태그 버튼이 클릭되었습니다.');
                if (tagsModal) {
                    tagsModal.style.display = 'block';
                    fetchTagsData();
                } else {
                    console.error('태그 모달을 찾을 수 없습니다.');
                }
            });
        } else {
            console.error('태그 버튼을 찾을 수 없습니다.');
        }

        // 선택한 태그 복사 버튼 이벤트 핸들러 (새로 추가)
        if (copySelectedTag) {
            copySelectedTag.addEventListener('click', function() {
                if (selectedTag) {
                    // 배포 태그 입력 필드에 자동으로 선택한 태그 입력
                    const deployTagInput = document.getElementById('deploy-tag');
                    if (deployTagInput) {
                        deployTagInput.value = selectedTag;
                    }
                    
                    // 태그 모달 닫기
                    if (tagsModal) {
                        tagsModal.style.display = 'none';
                    }
                    
                    // 배포 모달 열기
                    if (deployModal) {
                        deployModal.style.display = 'block';
                    }
                } else {
                    alert('먼저 태그를 선택해주세요.');
                }
            });
        }

        if (removeGithubInfoButton) {
            removeGithubInfoButton.addEventListener('click', function(event) {
                console.log('제거 버튼 클릭됨!');
                event.preventDefault();
                if (confirm('GitHub 계정 정보를 제거하시겠습니까?')) {
                    this.disabled = true; // 버튼 비활성화
                    window.removeGithubInfo();
                }
            });
        }

        // 배포 버튼 이벤트
        if (deploySubmit) {
            deploySubmit.addEventListener('click', function() {
                const appSelect = document.getElementById('deploy-app');
                const envSelect = document.getElementById('deploy-env');
                const tagInput = document.getElementById('deploy-tag');
                if (!appSelect || !envSelect || !tagInput) {
                    alert('필요한 입력 필드를 찾을 수 없습니다.');
                    return;
                }
                const app = appSelect.value;
                const env = envSelect.value;
                const tag = tagInput.value;
                if (!app || !env || !tag) {
                    alert('모든 필드를 입력해주세요.');
                    return;
                }
                fetch('/api/github/deploy', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        app: app,
                        env: env,
                        tag: tag
                    }),
                })
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Network response was not ok');
                    }
                    return response.json();
                })
                .then(data => {
                    if (data.status === 'success') {
                        alert('배포 요청이 성공적으로 전송되었습니다.');
                        if (deployModal) {
                            deployModal.style.display = 'none';
                        }
                    } else {
                        alert('배포 요청 중 오류가 발생했습니다: ' + (data.message || '알 수 없는 오류'));
                    }
                })
                .catch(error => {
                    console.error('배포 요청 중 오류 발생:', error);
                    alert('배포 요청 중 오류가 발생했습니다.');
                });
            });
        }

        // 서비스 교체 버튼 이벤트
        if (interchangeSubmit) {
            interchangeSubmit.addEventListener('click', function() {
                const appSelect = document.getElementById('interchange-app');
                const envSelect = document.getElementById('interchange-env');
                if (!appSelect || !envSelect) {
                    alert('필요한 입력 필드를 찾을 수 없습니다.');
                    return;
                }
                const app = appSelect.value;
                const env = envSelect.value;
                if (!app || !env) {
                    alert('모든 필드를 입력해주세요.');
                    return;
                }
                fetch('/api/github/interchange', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        app: app,
                        env: env
                    }),
                })
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Network response was not ok');
                    }
                    return response.json();
                })
                .then(data => {
                    if (data.status === 'success') {
                        alert('서비스 교체 요청이 성공적으로 전송되었습니다.');
                        if (interchangeModal) {
                            interchangeModal.style.display = 'none';
                        }
                    } else {
                        alert('서비스 교체 요청 중 오류가 발생했습니다: ' + (data.message || '알 수 없는 오류'));
                    }
                })
                .catch(error => {
                    console.error('서비스 교체 요청 중 오류 발생:', error);
                    alert('서비스 교체 요청 중 오류가 발생했습니다.');
                });
            });
        }

        // 새로고침 설정 관련 이벤트
        // refreshToggle 이벤트 리스너 함수 내부
        if (refreshToggle) {
            refreshToggle.addEventListener('change', function() {
                const isEnabled = this.checked;
                
                // meta refresh 태그를 즉시 업데이트
                const refreshMeta = document.getElementById('refresh-meta');
                if (refreshMeta) {
                    if (isEnabled) {
                        // 현재 설정된 간격 값 가져오기
                        const intervalSelect = document.getElementById('refresh-interval');
                        let intervalValue = parseInt(intervalSelect.value);
                        
                        // 사용자 지정 간격이 선택된 경우 해당 값 사용
                        if (intervalSelect.value === 'custom') {
                            const customIntervalValue = document.getElementById('custom-interval-value');
                            intervalValue = parseInt(customIntervalValue.value) || 10;
                        }
                        
                        refreshMeta.setAttribute('content', intervalValue.toString());
                    } else {
                        // 비활성화 시 매우 큰 값으로 설정하여 실질적으로 비활성화
                        refreshMeta.setAttribute('content', '999999999');
                    }
                }
                
                // 설정을 저장하기 위한 API 호출
                fetch('/api/refresh', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        enabled: isEnabled,
                    }),
                })
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Network response was not ok');
                    }
                    return response.json();
                })
                .then(data => {
                    if (data.status === 'success') {
                        if (isEnabled) {
                            // 자동 새로고침 활성화 시에만 페이지 리로드
                            // (meta 태그가 제거되었다면 다시 추가하기 위함)
                            window.location.reload();
                        }
                        // 비활성화 시에는 이미 meta 태그를 처리했으므로 리로드 불필요
                    }
                })
                .catch(error => {
                    console.error('새로고침 설정 변경 중 오류 발생:', error);
                });
            });
        }
        
        // 새로고침 간격 변경 이벤트
        if (refreshInterval && customIntervalContainer) {
            refreshInterval.addEventListener('change', function() {
                const selectedValue = this.value;
                if (selectedValue === 'custom') {
                    // 사용자 지정 간격 입력 필드 표시
                    customIntervalContainer.classList.add('active');
                    customIntervalContainer.style.display = 'flex';
                } else {
                    // 사용자 지정 간격 입력 필드 숨김
                    customIntervalContainer.classList.remove('active');
                    customIntervalContainer.style.display = 'none';
                    // 선택된 간격으로 새로고침 설정 업데이트
                    updateRefreshInterval(parseInt(selectedValue));
                }
            });
        }

        // 사용자 지정 간격 입력 이벤트
        if (customIntervalValue) {
            customIntervalValue.addEventListener('change', function() {
                const value = parseInt(this.value);
                if (value < 1) {
                    this.value = 1;
                    updateRefreshInterval(1);
                } else {
                    updateRefreshInterval(value);
                }
            });
        }

        // 수동 새로고침 버튼 클릭 이벤트
        if (manualRefreshButton) {
            manualRefreshButton.addEventListener('click', function() {
                const currentPath = window.location.pathname;
                const appMatch = currentPath.match(/\/dashboard\/([^\/]+)/);
                if (appMatch && appMatch[1]) {
                    // 앱 대시보드 페이지인 경우
                    const appName = appMatch[1];
                    fetch(`/api/manual_refresh/${appName}`)
                        .then(response => {
                            if (!response.ok) {
                                throw new Error('Network response was not ok');
                            }
                            return response.json();
                        })
                        .then(data => {
                            if (data.status === 'success') {
                                window.location.reload();
                            } else {
                                alert('새로고침 중 오류가 발생했습니다: ' + (data.message || '알 수 없는 오류'));
                            }
                        })
                        .catch(error => {
                            console.error('수동 새로고침 중 오류 발생:', error);
                            alert('수동 새로고침 중 오류가 발생했습니다.');
                        });
                } else {
                    // 메인 페이지인 경우 그냥 페이지 새로고침
                    window.location.reload();
                }
            });
        }

        // 페이지 로드 시 사용자 정의 간격 컨테이너 상태 설정
        if (refreshInterval && customIntervalContainer) {
            if (refreshInterval.value === 'custom') {
                customIntervalContainer.classList.add('active');
                customIntervalContainer.style.display = 'flex';
            } else {
                customIntervalContainer.classList.remove('active');
                customIntervalContainer.style.display = 'none';
            }
        }

        // 전역 이벤트: ESC 키를 누르면 모든 모달 닫기
        document.addEventListener('keydown', function(event) {
            if (event.key === 'Escape') {
                const modals = document.querySelectorAll('.modal');
                modals.forEach(modal => {
                    modal.style.display = 'none';
                });
            }
        });

        // 모달 외부 클릭 시 모달 닫기
        window.addEventListener('click', function(event) {
            const modals = document.querySelectorAll('.modal');
            modals.forEach(modal => {
                if (event.target === modal) {
                    modal.style.display = 'none';
                }
            });
        });
    }

    // GitHub 계정 정보 제거 함수 - 내부 함수로 정의
    function removeGithubInfo() {
        console.log('계정 정보 제거 함수 호출됨');
        fetch('/api/github/info/remove', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (data.status === 'success') {
                alert('GitHub 계정 정보가 제거되었습니다.');
                window.location.reload();
            } else {
                alert('GitHub 계정 정보 제거 중 오류가 발생했습니다: ' + (data.message || '알 수 없는 오류'));
            }
        })
        .catch(error => {
            console.error('GitHub 계정 정보 제거 중 오류 발생:', error);
            alert('GitHub 계정 정보 제거 중 오류가 발생했습니다.');
        });
    }

    // 새로고침 간격 업데이트 함수
    function updateRefreshInterval(interval) {
        fetch('/api/refresh', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                interval: interval,
            }),
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (data.status === 'success') {
                // 자동 새로고침 설정 변경
                const refreshMeta = document.getElementById('refresh-meta');
                const refreshToggle = document.getElementById('refresh-toggle');
                if (refreshMeta && refreshToggle && refreshToggle.checked) {
                    refreshMeta.setAttribute('content', interval.toString());
                }
            }
        })
        .catch(error => {
            console.error('새로고침 간격 변경 중 오류 발생:', error);
        });
    }

    // 태그 데이터 가져오기 함수
    function fetchTagsData() {
        console.log('태그 데이터를 가져오는 중...');
        
        const tagsLoading = document.getElementById('tags-loading');
        const tagsError = document.getElementById('tags-error');
        const repoTabs = document.getElementById('repo-tabs');
        const tagsList = document.getElementById('tags-list');
        
        if (!tagsLoading || !tagsError || !repoTabs || !tagsList) {
            console.error('태그 관련 DOM 요소를 찾을 수 없습니다:');
            console.error('tagsLoading:', tagsLoading);
            console.error('tagsError:', tagsError);
            console.error('repoTabs:', repoTabs);
            console.error('tagsList:', tagsList);
            return;
        }
        
        // 로딩 표시 및 초기화
        tagsLoading.style.display = 'block';
        tagsError.style.display = 'none';
        repoTabs.innerHTML = '';
        tagsList.innerHTML = '';
        
        // 이전에 이미 데이터를 가져왔으면 재사용
        if (tagsData) {
            console.log('기존 태그 데이터 재사용');
            renderTagsData(tagsData);
            tagsLoading.style.display = 'none';
            return;
        }
        
        // API 호출로 태그 정보 가져오기
        console.log('태그 API 호출 시작');
        fetch('/api/github/tags')
            .then(response => {
                console.log('API 응답 코드:', response.status);
                if (!response.ok) {
                    throw new Error(`태그 정보를 가져오는데 실패했습니다 (${response.status})`);
                }
                return response.json();
            })
            .then(data => {
                console.log('API 데이터 수신:', data);
                if (data.status === 'success') {
                    tagsData = data.data;
                    window.tagsData = data.data; // 전역 변수에도 저장
                    renderTagsData(tagsData);
                } else {
                    throw new Error(data.message || '태그 정보를 불러오는데 실패했습니다');
                }
            })
            .catch(error => {
                console.error('태그 정보 로딩 오류:', error);
                tagsError.style.display = 'block';
                const errorMessage = document.getElementById('tags-error-message');
                if (errorMessage) {
                    errorMessage.textContent = error.message;
                }
            })
            .finally(() => {
                tagsLoading.style.display = 'none';
            });
    }

    // 태그 데이터 렌더링 함수
    function renderTagsData(data) {
        console.log('태그 데이터 렌더링 시작');
        
        const repoTabs = document.getElementById('repo-tabs');
        const tagsList = document.getElementById('tags-list');
        
        if (!repoTabs || !tagsList) {
            console.error('태그 렌더링 DOM 요소를 찾을 수 없습니다.');
            return;
        }
        
        // 레포지토리 목록이 없거나 비어있을 경우
        if (!data || Object.keys(data).length === 0) {
            console.log('태그 데이터가 비어있습니다');
            tagsList.innerHTML = '<div class="empty-tags">태그 정보가 없습니다.</div>';
            return;
        }
        
        // 첫번째 레포지토리를 기본 선택
        if (!selectedRepo) {
            selectedRepo = Object.keys(data)[0];
            window.selectedRepo = selectedRepo; // 전역 변수에도 저장
        }
        
        console.log('선택된 레포지토리:', selectedRepo);
        
        // 레포지토리 탭 생성
        repoTabs.innerHTML = '';
        Object.keys(data).forEach(repo => {
            const tabElement = document.createElement('div');
            tabElement.className = 'repo-tab' + (repo === selectedRepo ? ' active' : '');
            tabElement.textContent = repo;
            tabElement.setAttribute('data-repo', repo);
            
            tabElement.addEventListener('click', function() {
                // 탭 선택 변경
                const allTabs = repoTabs.querySelectorAll('.repo-tab');
                allTabs.forEach(tab => tab.classList.remove('active'));
                this.classList.add('active');
                
                // 선택된 레포지토리 변경
                selectedRepo = this.getAttribute('data-repo');
                window.selectedRepo = selectedRepo; // 전역 변수에도 저장
                selectedTag = null; // 선택된 태그 초기화
                window.selectedTag = null; // 전역 변수에도 저장
                
                // 태그 목록 업데이트
                console.log('레포지토리 변경:', selectedRepo);
                updateTagsList(data[selectedRepo]);
            });
            
            repoTabs.appendChild(tabElement);
        });
        
        // 선택된 레포지토리의 태그 목록 표시
        updateTagsList(data[selectedRepo]);
    }

    // 태그 목록 업데이트 함수
    function updateTagsList(tags) {
        console.log('태그 목록 업데이트:', tags ? tags.length : 0, '개 태그');
        
        const tagsList = document.getElementById('tags-list');
        
        if (!tagsList) {
            console.error('태그 목록 DOM 요소를 찾을 수 없습니다.');
            return;
        }
        
        tagsList.innerHTML = '';
        
        if (!tags || tags.length === 0) {
            tagsList.innerHTML = '<div class="empty-tags">이 레포지토리에는 태그가 없습니다.</div>';
            return;
        }
        
        tags.forEach(tag => {
            const tagElement = document.createElement('div');
            tagElement.className = 'tag-item';
            tagElement.setAttribute('data-tag', tag.name);
            
            // 태그 항목 클릭 이벤트 처리
            tagElement.addEventListener('click', function() {
                // 이전에 선택된 태그 선택 해제
                const allTags = tagsList.querySelectorAll('.tag-item');
                allTags.forEach(t => t.classList.remove('selected'));
                
                // 현재 태그 선택
                this.classList.add('selected');
                selectedTag = this.getAttribute('data-tag');
                window.selectedTag = selectedTag; // 전역 변수에도 저장
                console.log('태그 선택됨:', selectedTag);
            });
            
            // 태그 정보 생성
            const tagNameElement = document.createElement('div');
            tagNameElement.className = 'tag-name';
            tagNameElement.textContent = tag.name;
            
            const tagDateElement = document.createElement('div');
            tagDateElement.className = 'tag-date';
            tagDateElement.textContent = '생성일: ' + tag.date;
            
            const tagCommitElement = document.createElement('div');
            tagCommitElement.className = 'tag-commit';
            tagCommitElement.textContent = '커밋: ' + tag.commit_sha;
            
            // 태그 요소에 추가
            tagElement.appendChild(tagNameElement);
            tagElement.appendChild(tagDateElement);
            tagElement.appendChild(tagCommitElement);
            
            // 태그 목록에 추가
            tagsList.appendChild(tagElement);
        });
    }

    // 전역 함수를 제공하지만, 실제 구현은 모듈 내부에 있음
    window.removeGithubInfo = removeGithubInfo;

    // DOMContentLoaded 이벤트에 이벤트 핸들러 등록 (한 번만!)
    document.addEventListener('DOMContentLoaded', initEventHandlers);
})();
