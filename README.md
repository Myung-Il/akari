# 🪄 Akari (아카리) - Extensible Discord Bot Platform

![Python](https://img.shields.io/badge/Python-3.10-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Discord.py](https://img.shields.io/badge/Discord.py-2.0+-5865F2?style=for-the-badge&logo=discord&logoColor=white)
![Architecture](https://img.shields.io/badge/Architecture-Modular(Cogs)-orange?style=for-the-badge)
![Platform](https://img.shields.io/badge/Platform-Render-black?style=for-the-badge&logo=render&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

**Akari**는 차세대 디스코드 커뮤니티를 위해 설계된 **확장형 멀티퍼포스(Multi-purpose) 봇 플랫폼**입니다.  

현재 **TTS(Text-to-Speech)** 핵심 모듈을 기반으로 24시간 무중단 서비스를 제공하고 있으며, 향후 미니게임 및 AI 챗봇 기능을 탑재할 수 있는 유연한 아키텍처로 설계되었습니다.

---

<br>
<br>
<br>

## 📑 프로젝트 보고서 (Project Report)

> **[📄 초기 프로젝트 보고서 보러가기 (PDF)](./docs/확장형%20멀티퍼포스%20디스코드%20봇%20'아카리(Akari)'%20초기%20인프라%20구축.pdf)**

## 📚 문서 (Documentation)
> **[프로젝트 기술 명세서 및 아키텍처 보러가기 (PDF)](docs/아카리%20기술%20명세서.pdf)**

## 🔗 봇 초대하기 (Invite)

> **[✨ 여기를 클릭하여 서버에 아카리 초대하기](https://discord.com/oauth2/authorize?client_id=1453854626410660055&permissions=1263234945908417&integration_type=0&scope=bot+applications.commands)**

---

<br>
<br>
<br>

## 🚀 주요 기능 (Key Features)

### 1. 🎙️ 스마트 오디오 시스템 (TTS Core)
* **Auto-Read:** 봇이 음성 채널에 상주하는 동안 입력된 텍스트를 실시간으로 감지하여 읽어줍니다.
* **Cross-Platform Engine:** 개발 환경(Windows)과 배포 환경(Linux)을 자동 감지하여 FFmpeg 경로를 동적으로 할당, 끊김 없는 음성을 송출합니다.

### 2. ⚡ 모듈형 아키텍처 (Modular Design)
* **Cogs System:** 기능별로 코드가 분리되어 있어, 봇을 종료하지 않고도 새로운 기능을 추가하거나 수정할 수 있는 확장성을 갖췄습니다.
* **Slash Commands:** 최신 디스코드 표준 인터페이스(`/`)를 전면 도입하여 직관적인 사용자 경험(UX)을 제공합니다.

### 3. ☁️ 24시간 무중단 클라우드 (Always-On)
* **Hybrid Hosting:** Render 클라우드 환경과 Flask 웹 서버(Keep-Alive)를 연동하여, 무료 호스팅의 한계인 절전 모드를 기술적으로 극복했습니다.

---

<br>
<br>
<br>

## 🗺️ 로드맵 (Roadmap)

아카리는 현재 **Phase 1** 단계를 완료하였으며, 지속적인 업데이트가 예정되어 있습니다.

- [x] **Phase 1: Foundation** (인프라 구축, TTS 모듈, 24시간 호스팅) ✅ **완료**
- [ ] **Phase 2: Entertainment** (주사위, 사다리 타기와 같은 미니게임 모듈)
- [ ] **Phase 3: AI Intelligence** (ChatGPT API 연동, 자연어 대화 기능)
- [ ] **Phase 4: Management** (서버 관리 및 유틸리티 기능 강화)

---

<br>
<br>
<br>

## 🛠️ 명령어 목록 (Commands)

| 명령어 | 설명 | 비고 |
| :--- | :--- | :--- |
| **/join** | 봇을 현재 접속한 음성 채널로 소환합니다. | TTS 모드 시작 |
| **/leave** | 봇을 음성 채널에서 내보냅니다. | 대기 모드 전환 |
| **/ping** | 봇의 현재 응답 속도(Latency)를 실시간으로 확인합니다. | 상태 점검 |

---

<br>
<br>
<br>

## 📂 프로젝트 구조 (Structure)

```text
akari/
├── bin/                 # FFmpeg 실행 파일 (Linux/Windows)
├── bot/                 # 봇 핵심 소스 코드
│   ├── commands/        # 기능별 모듈 (Cogs)
│   ├── client.py        # 봇 클라이언트 설정
│   └── config.py        # 환경변수 로더
├── docs/                # 프로젝트 보고서 및 문서
├── web/                 # Keep-Alive용 Flask 서버
├── build.sh             # Render 배포용 자동 빌드 스크립트
├── main.py              # 프로그램 진입점
└── requirements.txt     # 의존성 패키지 목록
```

---

<br>
<br>
<br>

## 💻 로컬 개발 환경 설정 (Development Setup)

이 프로젝트를 로컬 컴퓨터에서 실행하거나 기여(Contribute)하려면 아래 절차를 따르세요.

### 1. 사전 준비 (Prerequisites)

* **Python 3.10** 이상
* **Git** 설치
* **FFmpeg** 설치 및 시스템 환경 변수 등록 (Windows 필수)

### 2. 프로젝트 클론 및 가상환경 설정

```bash
# 1. 리포지토리 클론
git clone [GitHub_리포지토리_주소]
cd akari

# 2. 가상환경 생성
python -m venv venv

# 3. 가상환경 활성화 (Windows) ✨
venv\Scripts\activate
# (Mac/Linux의 경우: source venv/bin/activate)
```

### 3. 라이브러리 설치

가상환경이 활성화된 상태(`(venv)` 표시 확인)에서 필수 패키지를 설치합니다.
```bash
pip install -r requirements.txt
```

### 4. 환경 변수 설정 (.env)

프로젝트 최상위 폴더에 `.env` 파일을 생성하고 아래 내용을 입력하세요.
*(⚠️ 주의: 이 파일은 보안이 중요하므로 GitHub에 업로드하지 마세요.)*

```env
DISCORD_TOKEN=여기에_발급받은_봇_토큰_입력
```

### 5. 봇 실행

모든 설정이 완료되었다면 아래 명령어로 아카리를 실행합니다.
```bash
python main.py
```

---

<br>
<br>
<br>

## 🏗️ 기술 스택 (Tech Stack)

* **Language:** Python 3.10
* **Framework:** Discord.py 2.0+ (Asynchronous)
* **Audio Engine:** gTTS (Google Text-to-Speech)
* **Media Processing:** FFmpeg
* **Web Server:** Flask (Health Check System)
* **Infrastructure:** Render (PaaS), UptimeRobot

---

<br>
<br>
<br>

## 📝 라이선스 (License)

This project is licensed under the MIT License.