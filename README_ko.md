# ComfyUI-API-Pack

[English](README.md) | [한국어](README_ko.md)

외부 API를 호출하는 노드 모음입니다: 원격 ComfyUI API 실행, Grok 이미지-투-비디오, OpenAI 호환 추론.

## 설치 방법

1. 이 저장소를 ComfyUI의 `custom_nodes` 디렉터리에 클론하거나 복사합니다.
2. 의존성 설치:
   ```bash
   pip install -r requirements.txt
   ```
3. ComfyUI를 재시작합니다.

## 제공 노드

### API 노드 (`ApiPack/API`)

![API Workflow](workflows/comfyui-api-pack-workflow-API.png)

워크플로우를 원격 ComfyUI 인스턴스의 HTTP API로 실행합니다 (예: [RunPod](https://www.runpod.io/) 파드 또는 접근 가능한 임의의 ComfyUI). 모든 노드는 UI 워크플로우 포맷이 아니라 **API 포맷** 워크플로우 JSON(ComfyUI 메뉴: "Save (API Format)")을 받습니다. `api_url`은 원격 베이스 URL로, 예: `https://xxxx-8188.proxy.runpod.net/` 또는 `http://127.0.0.1:8188` 입니다.

| 노드 | 설명 |
|------|------|
| **Load Workflow** | `ComfyUI/user/default/workflows/`의 API 포맷 워크플로우 JSON을 읽어 STRING으로 반환합니다. |
| **Api Generate** | 워크플로우를 원격 ComfyUI에 보내 완료될 때까지 기다린 뒤 출력 이미지/프레임을 반환합니다. |
| **Api Submit** | Fire-and-forget 제출. 잡을 기록하고 즉시 `job_id`를 반환합니다 (대기하지 않음). |
| **Api Collect** | Api Submit으로 제출한 진행 중 잡을 수집합니다. 준비되면 프레임을 반환하고, 아니면 다운스트림을 차단합니다. |

#### Load Workflow

| 파라미터 | 타입 | 기본값 | 설명 |
|----------|------|--------|------|
| `filename` | ENUM | (필수) | `user/default/workflows/` 아래의 `.json` 파일 |

| 출력 | 설명 |
|------|------|
| `text` | 워크플로우 JSON 내용 |

#### Api Generate

| 파라미터 | 타입 | 기본값 | 설명 |
|----------|------|--------|------|
| `workflow` | STRING (입력) | (필수) | API 포맷 워크플로우 JSON 문자열 또는 파일 경로 |
| `positive_prompt` | STRING (입력) | (필수) | 포지티브 프롬프트. `positive_prompt_id`에 주입됨 |
| `positive_prompt_id` | STRING | (필수) | 포지티브 프롬프트를 받을 노드 id |
| `negative_prompt_id` | STRING | "" | `negative_prompt`(제공 시)를 받을 노드 id |
| `output_id` | STRING | "" | `images`/`gifs` 출력을 가져올 노드 id |
| `seed` | INT | -1 | `-1`이면 워크플로우의 기존 시드 유지 |
| `seed_id` | STRING | "" | `seed`/`noise_seed` 입력에 시드를 받을 노드 id |
| `api_url` | STRING | "" | 원격 ComfyUI 베이스 URL. 예: `https://xxxx-8188.proxy.runpod.net/` 또는 `http://127.0.0.1:8188` |
| `image_node_id` | STRING | "" | 업로드한 `image`를 받을 LoadImage 노드 id |
| `timeout_sec` | INT | 300 | 최대 폴링 시간(초) (1–36000) |
| `negative_prompt` | STRING (입력) | "" | 선택. 비어 있으면 건너뜀 |
| `image` | IMAGE | (선택) | 선택. 원격에 업로드되어 `image_node_id`에 바인딩됨 |
| `overrides` | STRING (입력) | "" | 선택. JSON `{node_id: <노드 전체 dict>}`. 각 항목이 **노드 전체를 교체**하며 마지막에 적용됨 |

| 출력 | 설명 |
|------|------|
| `output` | 디코드된 이미지/프레임 텐서 (애니메이션 출력은 프레임으로 펼쳐짐) |

#### Api Submit

입력은 **Api Generate**와 동일하며(`timeout_sec` 제외), 선택 `label`이 추가됩니다. OUTPUT_NODE라서 출력을 소비하는 노드가 없어도 실행됩니다.

| 파라미터 | 타입 | 기본값 | 설명 |
|----------|------|--------|------|
| `label` | STRING | "" | 선택. 잡과 함께 기록되는 라벨 (이후 Api Collect가 반환) |

| 출력 | 설명 |
|------|------|
| `job_id` | 제출된 잡 id (이미 진행 중인 잡이 있으면 빈 문자열) |

#### Api Collect

| 파라미터 | 타입 | 기본값 | 설명 |
|----------|------|--------|------|
| `wait_sec` | INT | 0 | `0`이면 준비됐을 때만 수집하고 아니면 즉시 건너뜀. 그 외엔 이 시간(초)까지 대기 (0–36000) |
| `poll_interval` | FLOAT | 2.0 | 대기 중 폴링 간격(초) (0.5–60.0) |

| 출력 | 설명 |
|------|------|
| `output` | 준비된 프레임. 없으면 다운스트림을 건너뛰는 `ExecutionBlocker` |
| `label` | 제출 시 기록된 라벨 |

> **종류별 단일 진행 잡:** API와 [Grok](#grok-노드-apipackgrok) 노드는 패키지 디렉터리의 단일 `jobs.lock`을 공유하지만 종류별로 슬롯이 분리됩니다 — API 잡과 Grok 잡이 동시에 진행될 수 있고, 각 종류는 하나만 허용됩니다. 해당 종류의 잡이 이미 진행 중이면 Submit은 건너뛰고, Collect가 완료되면 슬롯을 비웁니다. `/loop` 등으로 Collect를 반복 실행하면 완료된 결과를 받아올 수 있습니다.

---

### Grok 노드 (`ApiPack/Grok`)

| 노드 | 설명 |
|------|------|
| **Grok Generate** | 이미지 한 장으로 Grok Imagine I2V 영상 클립을 만들어 output 폴더에 네이티브 VIDEO로 저장합니다 (노드에서 인라인 미리보기 제공). |
| **Grok Submit** | Fire-and-forget 제출. 생성 요청만 보내고 즉시 `request_id`를 반환합니다 (대기하지 않음). |
| **Grok Collect** | Grok Submit으로 제출한 진행 중 잡을 수집합니다. 준비되면 VIDEO를 반환하고, 아니면 다운스트림을 차단합니다. |

#### Grok Generate

| 파라미터 | 타입 | 기본값 | 설명 |
|----------|------|--------|------|
| `image` | IMAGE | (필수) | 소스 이미지 (첫 프레임) |
| `prompt` | STRING | "" | 움직임/연출 설명 (선택) |
| `duration` | INT | 5 | 영상 길이(초) (1–15) |
| `resolution` | ENUM | "720p" | "720p" 또는 "480p" |
| `model` | STRING | "grok-imagine-video-1.5-preview" | Grok 영상 모델 |
| `filename_prefix` | STRING | "grok/GrokVideo" | ComfyUI output 디렉터리 기준 저장 경로 접두사 |
| `poll_interval` | INT | 5 | 상태 폴링 간격(초) (1–60) |
| `timeout` | INT | 600 | 생성 대기 최대 시간(초) (30–3600) |
| `access_token` | STRING | "" | 선택. 비우면 `GROK_ACCESS_TOKEN` 환경변수 사용 |
| `refresh_token` | STRING | "" | 선택. 비우면 `GROK_REFRESH_TOKEN` 환경변수 사용 |
| `client_id` | STRING | "" | 선택. 비우면 `GROK_CLIENT_ID` 환경변수 사용 |

| 출력 | 설명 |
|------|------|
| `video` | 생성된 클립(소리 포함). 노드에서 인라인 미리보기로도 표시됨 |

> **자격증명:** 세 토큰을 노드 입력으로 직접 넣거나, 비워 두면 `GROK_ACCESS_TOKEN` / `GROK_REFRESH_TOKEN` / `GROK_CLIENT_ID` 환경변수에서 읽습니다. 401/403 발생 시 access token은 자동 갱신됩니다.

#### Grok Submit

입력은 **Grok Generate**와 동일하며(`poll_interval`/`timeout` 제외), 선택 `label`이 추가됩니다. OUTPUT_NODE라서 출력을 소비하는 노드가 없어도 실행됩니다. mp4 저장 경로는 제출 시점에 예약되어 lock에 기록되고, 클립이 준비되면 Collect가 그 경로에 저장합니다.

| 파라미터 | 타입 | 기본값 | 설명 |
|----------|------|--------|------|
| `label` | STRING | "" | 선택. 잡과 함께 기록되는 라벨 (이후 Grok Collect가 반환) |

| 출력 | 설명 |
|------|------|
| `request_id` | 제출된 잡의 request id (이미 진행 중인 Grok 잡이 있으면 빈 문자열) |

#### Grok Collect

| 파라미터 | 타입 | 기본값 | 설명 |
|----------|------|--------|------|
| `wait_sec` | INT | 0 | `0`이면 준비됐을 때만 수집하고 아니면 즉시 건너뜀. 그 외엔 이 시간(초)까지 대기 (0–3600) |
| `poll_interval` | FLOAT | 5.0 | 대기 중 폴링 간격(초) (0.5–60.0) |
| `access_token` | STRING | "" | 선택. 비우면 `GROK_ACCESS_TOKEN` 환경변수 사용 |
| `refresh_token` | STRING | "" | 선택. 비우면 `GROK_REFRESH_TOKEN` 환경변수 사용 |
| `client_id` | STRING | "" | 선택. 비우면 `GROK_CLIENT_ID` 환경변수 사용 |

| 출력 | 설명 |
|------|------|
| `video` | 준비된 클립. 없으면 다운스트림을 건너뛰는 `ExecutionBlocker` |
| `label` | 제출 시 기록된 라벨 |

> **수거 시 자격증명:** Collect도 Grok API를 호출(폴링/다운로드)하므로 토큰을 입력 또는 환경변수에서 다시 읽습니다 — 토큰은 lock 파일에 저장하지 **않습니다**. Grok Generate와 같은 방식으로 넣어 주세요.

> **종류별 단일 진행 잡:** Grok과 [API](#api-노드-apipackapi) 노드는 패키지 디렉터리의 단일 `jobs.lock`을 공유하지만 종류별로 슬롯이 분리됩니다 — Grok 잡과 API 잡이 동시에 진행될 수 있고, 각 종류는 하나만 허용됩니다. 해당 종류의 잡이 이미 진행 중이면 Submit은 건너뛰고, Collect가 완료되면 슬롯을 비웁니다. `/loop` 등으로 Collect를 반복 실행하면 완료된 클립을 받아올 수 있습니다.

---

### 추론 노드 (`ApiPack/Inference`)

![Inference Workflow](workflows/comfyui-api-pack-workflow-Inference.png)

| 노드 | 설명 |
|------|------|
| **OpenAI Inference** | OpenAI 호환 API로 텍스트 생성. 비전 및 씽킹 모드 지원. |

#### OpenAI Inference

OpenAI 호환 백엔드를 하나의 노드로 모두 처리합니다 — OpenAI, vLLM, Ollama의 `/v1` 엔드포인트, Gemini의 OpenAI 호환 엔드포인트. `base_url`/`api_key`/`model`만 원하는 서버로 지정하면 됩니다.

| 파라미터 | 타입 | 기본값 | 설명 |
|----------|------|--------|------|
| `prompt` | STRING | "Hello, world!" | 사용자 프롬프트 |
| `system_instruction` | STRING | "You are a helpful assistant." | 시스템 프롬프트 |
| `base_url` | STRING | "" | API base URL, 예: `https://api.openai.com/v1` (`.env`의 `OPENAI_BASE_URL`로 설정 가능) |
| `api_key` | STRING | "" | API 키 (`.env`의 `OPENAI_API_KEY`로 설정 가능) |
| `model` | STRING | "" | 모델명. 비우면 `/models`에 모델이 하나일 때 자동 감지 |
| `max_output_tokens` | INT | 100 | 최대 출력 토큰 (최대 131072) |
| `seed` | INT | 0 | 랜덤 시드 |
| `temperature` | FLOAT | 0.7 | 샘플링 온도 (0.0–2.0) |
| `think` | BOOLEAN | False | 씽킹 모드 활성화 |
| `image` | IMAGE | (선택) | 비전 작업용 입력 이미지 |

| 출력 | 설명 |
|------|------|
| `response` | 모델의 답변 (`<think>` 블록은 제거됨) |
| `reasoning` | 사고 과정. `reasoning_content` 필드 또는 인라인 `<think>...</think>` 블록에서 추출 (없으면 빈 문자열) |

> **참고:** 응답은 인메모리 캐싱됩니다 (LRU, 최근 10개 입력 조합) — 완전히 동일한 요청을 다시 실행하면 API 호출 없이 캐시된 응답을 반환합니다.

## 설정

> **`.env`는 선택 사항입니다** — 없어도 팩은 항상 정상 로드됩니다. [`.env.example`](.env.example)을 `.env`로 복사한 뒤 필요한 변수만 채우세요 (또는 같은 값을 노드 입력으로 전달). 자격증명이 필요한 노드가 값을 못 찾으면 **실행 시점에** 명확한 에러(ComfyUI 에러 창)를 띄웁니다 — 로딩 단계에선 절대 죽지 않습니다.

### OpenAI Inference 기본값 (`.env` 또는 노드 입력)

**OpenAI Inference** 노드는 먼저 노드 입력에서 `base_url`/`api_key`를 읽고, 입력이 비어 있으면 아래 `.env` 변수를 폴백으로 사용합니다:

```
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_API_KEY=your-api-key
```

### Grok 자격증명 (`.env` 또는 노드 입력)

**Grok** 노드(Generate / Submit / Collect)는 자격증명을 노드 입력에서 먼저 읽고, 입력이 비어 있으면 아래 `.env` 변수로 대체합니다:

```
GROK_ACCESS_TOKEN=...
GROK_REFRESH_TOKEN=...
GROK_CLIENT_ID=...
```

access token은 401/403에서 자동 갱신됩니다. `Grok token refresh failed (...)` 에러가 뜨면 refresh token이나 client_id가 만료/폐기된 것이니, x.ai에서 다시 인증해 값을 갱신하세요.

## 라이선스

GPL-3.0 License
