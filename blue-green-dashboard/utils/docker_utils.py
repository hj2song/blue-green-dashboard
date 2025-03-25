import subprocess

def run_command(command):
    """주어진 명령어를 실행하고 결과를 반환합니다."""
    try:
        result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {command}")
        print(f"Error: {e}")
        return ""

def get_service_info(service_name):
    """서비스의 레플리카 수, 이미지 태그, 포트 포워딩 정보를 가져옵니다."""
    # 레플리카 수 추출
    replicas = run_command(f"docker service ls --filter name={service_name} --format '{{{{.Replicas}}}}' 2>/dev/null")
    if not replicas:
        return None, None, None

    # 이미지 태그 추출
    image_with_tag = run_command(f"docker service ls --filter name={service_name} --format '{{{{.Image}}}}' 2>/dev/null")
    tag = image_with_tag.split(":")[-1] if ":" in image_with_tag else "latest"

    # 포트 포워딩 정보 추출
    port_forwarding = "N/A"  # 기본값
    try:
        port_cmd = (
            f"docker service inspect {service_name} --format "
            f"'{{{{range .Endpoint.Ports}}}}{{{{.PublishedPort}}}}:{{{{.TargetPort}}}}{{{{end}}}}' 2>/dev/null"
        )
        port_output = run_command(port_cmd).strip()
        if port_output:
            port_forwarding = port_output.split("\n")[0] if "\n" in port_output else port_output
        else:
            port_cmd_fallback = (
                f"docker service inspect {service_name} --format "
                f"'{{{{range .Spec.EndpointSpec.Ports}}}}{{{{.PublishedPort}}}}:{{{{.TargetPort}}}}{{{{end}}}}' 2>/dev/null"
            )
            port_output_fallback = run_command(port_cmd_fallback).strip()
            if port_output_fallback:
                port_forwarding = port_output_fallback.split("\n")[0] if "\n" in port_output_fallback else port_output_fallback
    except Exception as e:
        print(f"Error extracting port forwarding for {service_name}: {e}")

    return replicas, tag, port_forwarding
