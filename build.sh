#!/usr/bin/env bash
# 에러 발생 시 즉시 중단
set -o errexit

# 1. 파이썬 라이브러리 설치
pip install -r requirements.txt

# 2. 리눅스용 FFmpeg 다운로드 (없을 경우에만)
if [ ! -f ./bin/ffmpeg ]; then
    echo "⬇️ Linux용 FFmpeg 다운로드 중..."
    mkdir -p bin
    # 정적 빌드 다운로드
    wget https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz
    # 압축 해제
    tar -xf ffmpeg-release-amd64-static.tar.xz
    # 실행 파일만 bin 폴더로 이동
    mv ffmpeg-*-static/ffmpeg ./bin/ffmpeg
    # 임시 파일 정리
    rm -rf ffmpeg-*-static ffmpeg-release-amd64-static.tar.xz
    # 실행 권한 부여
    chmod +x ./bin/ffmpeg
    echo "✅ FFmpeg 설치 완료!"
fi