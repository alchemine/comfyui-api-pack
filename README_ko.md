# ComfyUI-API-Pack

[English](README.md) | [한국어](README_ko.md)

외부 API를 호출하는 노드 모음입니다. llama-server로 zero-shot 분류를 하고, OpenAI 호환 API로 추론하고,
원격 ComfyUI에서 워크플로를 실행하고, Grok으로 이미지를 비디오로 만듭니다.

## 예시

![Workflow](workflows/comfyui-api-pack-workflow-ZeroShot.png)

zero-shot 워크플로는 고객 메시지 하나에 질문 세 개를 던집니다. **Zero-Shot Classification**이 한 번의 요청으로 모두 답하고
질문마다 한 줄씩 출력하며, **Zero-Shot Answer**가 그중 `route`의 답을 꺼냅니다.

![Inference Workflow](workflows/comfyui-api-pack-workflow-Inference.png)

추론 워크플로는 **OpenAI Inference**로 프롬프트를 쓰고, 그 프롬프트로 이미지를 생성합니다.

![API Workflow](workflows/comfyui-api-pack-workflow-API.png)

API 워크플로는 **Load Workflow**로 워크플로를 읽어 원격 ComfyUI에서 실행합니다. 한 번은 **Api Generate**로,
한 번은 **Api Submit**과 **Api Collect**로 실행합니다.

## 사용법

### Zero-Shot Classification

`questions`에 라벨을 적고 `state`에 글을 넣은 뒤, `summary`와 `answers`에서 답을 받습니다. 이 노드는
[clef-flash](https://huggingface.co/Cloudflare/clef-flash) 같은 결정 모델을 올린 llama-server의 `/v1/systemone`을
부릅니다. 이 모델은 글을 생성하지 않고, forward 한 번으로 라벨마다 확률을 매깁니다.

| 위젯 | 하는 일 |
|------|---------|
| `state` | 분류할 내용 |
| `questions` | 질문 id를 키로 한 질문 객체의 JSON. 아래 참고 |
| `base_url` | llama-server 주소. 기본값 `http://localhost:8082` |
| `api_key` | 값이 있으면 Bearer 토큰으로 보냅니다 |
| `model` | 값이 있으면 보냅니다. 모델이 하나뿐인 서버는 무시합니다 |
| `image` (입력) | state 앞에 놓이는 이미지. 배치의 장마다 하나씩 보냅니다. 서버를 `--mmproj`로 띄워야 합니다 |
| `answers` (출력) | 응답의 `answers`를 들여쓴 JSON. 키는 질문 id입니다 |
| `summary` (출력) | 질문마다 `id: value (score)` 한 줄. value와 score는 **Zero-Shot Answer**와 같습니다 |

| 타입 | `criteria` | 답 |
|------|------------|----|
| `choice` | `{"선택지": "설명" 또는 null, ...}` | `choice`, `confidence`, `probabilities` |
| `score` | `["가장 낮음", ..., "가장 높음"]`, 2~10단계 | 기댓값 `score`, `confidence`, `legend`, `probabilities` |
| `noul` | 선택. `{"true": "설명", "false": "설명"}` | `noul`, 참일 확률 |

```json
{
  "route": {
    "type": "choice",
    "instructions": "어느 팀이 이 문의를 처리해야 하나?",
    "criteria": {"billing": "결제, 환불, 청구서", "technical": "버그, 장애, 로그인 문제"}
  },
  "urgency": {"type": "score", "instructions": "얼마나 긴급한가?", "criteria": ["나중에 처리해도 됨", "이번 주", "오늘"]},
  "outage": {"type": "noul", "instructions": "서비스가 멈췄는가?"}
}
```

state가 `결제 페이지에서 오류가 나서 주문이 막혔어요.`일 때 `summary`는 이렇습니다.

```
route: billing (0.76)
urgency: 오늘 (1.89)
outage: false (0.24)
```

입력이 같으면 답도 늘 같습니다. `temperature`, `top_k`, `top_p`, `seed`는 없습니다. 아무것도 샘플링하지 않고,
확률의 스케일은 모델 파일이 정합니다.

### OpenAI Inference

프롬프트를 **OpenAI Inference**에 넣고 `response`에서 답을 받습니다. OpenAI, vLLM, Ollama의 `/v1` 엔드포인트,
Gemini의 OpenAI 호환 엔드포인트 등 OpenAI 호환 백엔드면 모두 됩니다.

| 위젯 | 하는 일 |
|------|---------|
| `prompt` / `system_instruction` | 사용자 프롬프트와 시스템 프롬프트 |
| `base_url` | API 주소. 예: `https://api.openai.com/v1`. 비우면 `OPENAI_BASE_URL`을 읽습니다 |
| `api_key` | 비우면 `OPENAI_API_KEY`를 읽습니다 |
| `model` | 비우면 서버의 `/models`에 모델이 하나뿐일 때 그것을 씁니다 |
| `max_output_tokens` | 최대 131072. 기본값 100 |
| `seed` / `temperature` | 샘플링. `temperature`는 0.0~2.0, 기본값 0.7 |
| `think` | thinking 모드를 켭니다 |
| `image` (입력) | 비전 모델에 넣을 이미지 |
| `response` (출력) | 답. `<think>` 블록은 뺍니다 |
| `reasoning` (출력) | `reasoning_content`나 본문의 `<think>...</think>` 블록에서 꺼낸 생각 과정. 없으면 빈 문자열 |

서로 다른 요청 10개까지 메모리에 캐시합니다. 같은 요청을 다시 실행하면 API를 부르지 않습니다.

### Api Generate / Api Submit / Api Collect

[RunPod](https://www.runpod.io/) pod 같은 원격 ComfyUI에서 HTTP API로 워크플로를 실행합니다. 워크플로는 UI 형식이
아니라 **API 형식** JSON입니다(ComfyUI 메뉴: "Save (API Format)"). **Api Generate**는 결과를 기다리고,
**Api Submit**은 `job_id`를 바로 돌려주며 **Api Collect**가 나중에 결과를 받아옵니다.

| 위젯 | 하는 일 |
|------|---------|
| `workflow` (입력) | API 형식 워크플로 JSON 또는 그 파일 경로. **Load Workflow**로 `user/default/workflows/`에서 읽을 수 있습니다 |
| `api_url` | 원격 ComfyUI 주소. 예: `https://xxxx-8188.proxy.runpod.net/`, `http://127.0.0.1:8188` |
| `positive_prompt` (입력) / `positive_prompt_id` | 프롬프트와 그것을 받을 노드 id |
| `negative_prompt` (입력) / `negative_prompt_id` | 네거티브 프롬프트도 같습니다. 비어 있으면 건너뜁니다 |
| `seed` / `seed_id` | seed와 그것을 `seed`/`noise_seed`로 받을 노드. `-1`이면 워크플로의 seed를 그대로 둡니다 |
| `image` (입력) / `image_node_id` | 원격에 올려 그 LoadImage 노드에 연결할 이미지 |
| `output_id` | `images`/`gifs` 출력을 가져올 노드. 애니메이션은 프레임으로 펼칩니다 |
| `overrides` (입력) | JSON `{node_id: <노드 전체>}`. 항목마다 노드 전체를 바꾸며, 마지막에 적용합니다 |
| `timeout_sec` | Api Generate만. 폴링 제한 시간(초), 기본값 300 |
| `label` | Api Submit만. 잡과 함께 기록되고 Api Collect가 돌려줍니다 |
| `wait_sec` / `poll_interval` | Api Collect만. `wait_sec`가 0이면 준비됐을 때만 받고 아니면 바로 건너뜁니다 |

Api Collect는 잡이 끝났으면 프레임을 돌려줍니다. 아니면 `ExecutionBlocker`를 돌려주고, 그 뒤의 노드는 건너뜁니다.

### Grok Generate / Grok Submit / Grok Collect

이미지 한 장을 Grok Imagine 비디오 클립으로 만들어, 출력 폴더에 미리보기가 붙은 VIDEO로 저장합니다.
**Grok Generate**는 클립을 기다리고, **Grok Submit**은 `request_id`를 바로 돌려주며 **Grok Collect**가 나중에 클립을
받아옵니다.

| 위젯 | 하는 일 |
|------|---------|
| `image` (입력) | 첫 프레임 |
| `prompt` | 움직임이나 장면 설명. 선택 |
| `duration` / `resolution` | 1~15초, `720p` 또는 `480p` |
| `model` | 기본값 `grok-imagine-video-1.5-preview` |
| `filename_prefix` | ComfyUI 출력 폴더 아래 경로. 기본값 `grok/GrokVideo` |
| `poll_interval` / `timeout` | Grok Generate의 폴링. 기본값 5초와 600초 |
| `access_token` / `refresh_token` / `client_id` | 비우면 `GROK_ACCESS_TOKEN` / `GROK_REFRESH_TOKEN` / `GROK_CLIENT_ID`를 읽습니다. access token은 401/403에서 스스로 갱신됩니다 |
| `label` | Grok Submit만. 잡과 함께 기록되고 Grok Collect가 돌려줍니다 |
| `wait_sec` / `poll_interval` | Grok Collect만. `wait_sec`가 0이면 준비됐을 때만 받고 아니면 바로 건너뜁니다 |

Grok Collect도 Grok API를 부르므로 토큰이 필요합니다. 토큰은 잡과 함께 저장하지 않습니다.

API 노드와 Grok 노드는 팩 디렉터리의 `jobs.lock`에 종류마다 진행 중인 잡을 하나씩 둡니다. 같은 종류의 잡이 진행 중이면
Submit은 건너뛰고, Collect가 끝나면 자리를 비웁니다. `/loop` 등으로 Collect를 반복 실행하면 끝난 결과를 받아옵니다.

## 설치

ComfyUI Manager에서 **ComfyUI-API-Pack**을 검색하거나:

```bash
cd ComfyUI/custom_nodes
git clone https://github.com/alchemine/comfyui-api-pack
pip install -r comfyui-api-pack/requirements.txt
```

## 노드

`ApiPack/Inference`

**Zero-Shot Answer**: Zero-Shot Classification의 `answers`에서 질문 하나를 꺼냅니다.

| 출력 | `choice` | `score` | `noul` |
|------|----------|---------|--------|
| `value` (STRING) | 고른 선택지 | 가장 가까운 단계의 설명 | 확률이 0.5 이상이면 `"true"`, 아니면 `"false"` |
| `score` (FLOAT) | 고른 선택지의 확률 | 단계의 기댓값 | 참일 확률 |
| `confidence` (FLOAT) | `confidence` | `confidence` | `\|2p - 1\|`. 선택지 두 개짜리 `choice`와 같은 식 |

`ApiPack/API`

**Load Workflow**: `user/default/workflows/`의 API 형식 워크플로 JSON을 STRING으로 읽습니다.

## 설정

`.env`는 없어도 됩니다. [`.env.example`](.env.example)을 `.env`로 복사하고 쓰는 값만 채우면 됩니다. 노드 입력이
`.env`보다 우선합니다. 자격 증명이 없으면 팩을 불러올 때가 아니라 노드를 실행할 때 오류가 납니다.

```
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_API_KEY=your-api-key

GROK_ACCESS_TOKEN=...
GROK_REFRESH_TOKEN=...
GROK_CLIENT_ID=...
```

`Grok token refresh failed (...)` 오류는 refresh token이나 client_id가 만료되었거나 취소되었다는 뜻입니다.
x.ai에서 다시 인증하고 값을 바꾸세요.

## 라이선스

GPL-3.0. [LICENSE](LICENSE)를 보세요.
