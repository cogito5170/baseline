# Personal Wealth OS — 제품 사양 (사용자 원문, 2026-10-05)

이 파일은 사용자 요구사항 원문이다. 바꾸지 않는다. 해석 · 설계는 프로젝트 저장소의 /docs 에 둔다.

## 1. 프로젝트 목표

일반 사용자가 자신의 다양한 자산을 하나의 플랫폼에서 관리하고, 전체 자산 상태를 기반으로 포트폴리오를 분석·시뮬레이션·전략화할 수 있는 대중형 웹 플랫폼을 개발한다.

단순 주식/코인 조회 앱이 아니다. 핵심 제품은 "내 전체 자산을 지금 어떻게 운영해야 하는가?"라는 질문에 데이터를 기반으로 답하는 Personal Wealth Operating System이다.

## 2. 지원 자산

초기부터 모든 자산을 실제 금융기관과 연동할 필요는 없다. 도메인 모델은 다음 자산을 수용할 수 있도록 설계한다.

- 국내 주식
- 해외 주식
- ETF
- 채권
- 예금/현금
- 가상자산
- 부동산
- 경매 자산
- 기타 대체자산

향후 새로운 asset type을 추가할 수 있도록 extensible한 구조를 사용한다.

## 3. 핵심 사용자 흐름

1. 사용자가 가입한다.
2. 자산을 등록한다.
3. 전체 자산을 하나의 Portfolio로 통합한다.
4. 플랫폼이 현재 Portfolio State를 계산한다.
5. 위험도, 자산배분, 유동성, 집중도, 변동성 등을 분석한다.
6. 사용자가 목표를 설정한다. 예: 자산 증식, 안정적인 현금흐름, 특정 기간까지 목표금액 달성, 위험 최소화, 특정 자산 비중 유지.
7. 플랫폼이 여러 전략을 시뮬레이션한다.
8. 사용자에게 전략과 근거를 보여준다.
9. 사용자가 선택한다.
10. 실제 주문/거래는 초기 버전에서는 사용자가 직접 수행한다.

## 4. 핵심 아키텍처

다음 구조를 기본 설계로 사용한다.

```
                    Web Client
                        │
                        ▼
                   API Gateway
                        │
        ┌───────────────┼────────────────┐
        ▼               ▼                ▼
    User Service   Portfolio Service   Market Data
        │               │                │
        └───────────────┼────────────────┘
                        ▼
                  Portfolio State
                        │
          ┌─────────────┼─────────────┐
          ▼             ▼             ▼
       Valuation       Risk        Liquidity
          │             │             │
          └─────────────┼─────────────┘
                        ▼
                 Strategy Engine
                        │
          ┌─────────────┼─────────────┐
          ▼             ▼             ▼
      Allocation     Scenario      Opportunity
          │          Simulation       Engine
          └─────────────┼─────────────┘
                        ▼
                 Strategy Proposal
                        │
                        ▼
                  Policy / Guard
                        │
                        ▼
                       User
```

## 5. 중요한 설계 원칙

### 5.1 AI를 시스템의 결정권자로 만들지 않는다.

LLM은 분석과 제안에 사용한다. LLM이 직접 다음을 수행해서는 안 된다.

- 임의의 주문 실행
- 임의의 자산 변경
- 사용자 포트폴리오 변경
- 금융 데이터 조작
- 위험 한도 우회

AI의 역할은 Data → Analysis → Explanation → Strategy Proposal 이다. 실제 허용 여부는 deterministic한 시스템이 판단한다: AI Proposal → Policy → Risk Constraint → User Confirmation → Execution.

## 6. Portfolio State

각 사용자는 하나 이상의 Portfolio를 가질 수 있다. Portfolio State에는 최소한 다음 정보가 포함되어야 한다.

- total value
- cash
- asset allocation
- realized P&L
- unrealized P&L
- exposure
- volatility
- drawdown
- concentration
- liquidity
- currency exposure
- target allocation
- risk profile
- investment horizon

모든 계산 결과에는 데이터의 기준 시점(timestamp)을 기록한다.

## 7. Portfolio 전략

사용자가 목표 비중을 직접 설정할 수 있어야 한다. 예:

| 자산군 | 목표 비중 |
|---|---|
| US Equity | 30% |
| KR Equity | 20% |
| Bond | 20% |
| Crypto | 10% |
| Cash | 20% |

시스템은 현재 비중과 목표 비중의 차이를 계산한다: Target → Current → Deviation → Scenario → Rebalancing Proposal.

단순히 "매수/매도"만 보여주지 말고 여러 전략을 비교한다. 예: Conservative, Balanced, Growth, High Risk, User Custom.

## 8. Scenario Engine

사용자가 가상의 상황을 테스트할 수 있어야 한다. 예:

- BTC가 -30% 하락하면 내 전체 자산은 어떻게 되는가?
- 미국 주식이 -20%가 되면?
- 금리가 상승하면?
- 현금 비중을 10% 증가시키면?
- 5년 동안 매월 100만원을 투자하면?

시스템은 Portfolio 전체에 미치는 영향을 계산한다: Scenario → Portfolio Simulation → Risk Metrics → Outcome Distribution. 결과에는 반드시 가정과 데이터 기준을 표시한다.

## 9. 경매 / 대체자산

경매 자산을 별도의 asset type으로 지원한다. Auction Asset은 다음 항목을 가진다.

- estimated value
- bid price
- acquisition cost
- tax
- maintenance cost
- expected exit price
- expected holding period
- estimated return

단순 예상 수익률만 계산하지 않는다. 전체 Portfolio에 편입했을 때 Before Portfolio → Add Auction Asset → After Portfolio → Risk / Liquidity / Concentration 을 비교한다.

핵심 질문은 "이 자산이 좋은가?"가 아니라 "이 자산을 내 전체 포트폴리오에 추가하는 것이 합리적인가?"이다.

## 10. 데이터 신뢰성

금융 데이터는 반드시 provenance를 관리한다. 각 데이터에 source, timestamp, instrument, currency, price, data_status 를 기록한다.

데이터 상태는 최소한 다음처럼 구분한다: OBSERVED, CALCULATED, ESTIMATED, USER_PROVIDED, MOCK, UNAVAILABLE.

실제 데이터와 mock 데이터를 절대로 조용히 섞지 않는다.

## 11. AI Analyst

AI는 여러 전문 역할로 분리할 수 있다: Portfolio Analyst, Equity Analyst, Crypto Analyst, Macro Analyst, Risk Analyst, Alternative Asset Analyst.

각 Agent는 자신의 분석 결과를 제출한다. 하지만 최종 전략은 Agent의 단순 투표 결과가 아니다. Evidence → Analysis → Proposal → Policy → Final Strategy 구조를 사용한다.

## 12. 사용자에게 보여줄 핵심 화면

Dashboard 예시:

| 항목 | 예시 값 |
|---|---|
| Total Wealth | ₩ XXX,XXX,XXX |
| Today's Change | +₩ XXX,XXX |
| Risk | Medium |
| Liquidity | Good |
| Target Deviation | +6.4% |
| Portfolio Health | 82 / 100 |

그리고 "오늘 확인할 사항"을 제공한다. 예:

- 미국 주식 비중이 목표보다 5.2% 높습니다.
- 이번 달 예정된 현금 지출을 고려하면 현금성 자산이 부족할 수 있습니다.

모든 판단에는 근거를 표시한다.

## 13. Opportunity Feed

사용자가 관심 있는 투자 기회를 발견할 수 있는 화면을 만든다. 예:

| 항목 | 지표 1 | 지표 2 | 지표 3 |
|---|---|---|---|
| US ETF | Target allocation deviation: +4.2% | Risk: Medium | |
| BTC | Volatility increased 18% | Portfolio impact: High | |
| Auction | Estimated discount: 12% | Liquidity: Low | Portfolio correlation: Low |

단순 추천 리스트가 아니라 "현재 내 Portfolio에 어떤 영향을 주는가"를 중심으로 보여준다.

## 14. MVP 범위

첫 번째 버전에서 실제 금융기관 API 연동이나 실제 거래 실행을 구현하지 않는다.

반드시 구현:

- 회원가입 / 로그인
- Portfolio 생성
- 자산 등록
- 거래내역 등록
- 현재 자산가치 계산
- Portfolio Dashboard
- Asset Allocation
- Risk Analysis
- Target Allocation
- Rebalancing Simulation
- Scenario Simulation
- Strategy Proposal
- 데이터 provenance
- 사용자별 Portfolio 저장

나중에 구현:

- 증권사 API
- 거래소 API
- 은행 API
- 실제 주문
- 자동 리밸런싱
- 결제
- 실시간 금융 데이터
- 경매 데이터 자동 수집
- 금융상품 제휴

## 15. 기술 요구사항

웹 기반 대규모 시스템을 전제로 설계한다. 권장 구조: Frontend → Backend API → Domain Services → Database → Event / Queue → Analytics / Strategy.

처음부터 불필요하게 microservice를 남발하지 않는다. Modular Monolith → 필요한 부분만 Service 분리 전략을 사용한다. 모든 domain boundary를 명확하게 정의한다.

## 16. 중요한 Domain

최소 다음 domain을 분리한다: Identity, User, Portfolio, Asset, Transaction, MarketData, Valuation, Risk, Strategy, Scenario, Opportunity, Notification, Audit.

각 domain의 책임과 interface를 명확히 정의한다.

## 17. 보안

금융 플랫폼이므로 보안을 핵심 기능으로 취급한다. 반드시 고려할 것:

- authentication
- authorization
- encryption
- secrets management
- audit log
- rate limiting
- input validation
- CSRF/XSS/SQL injection 방어
- 개인정보 최소 수집
- 민감정보 암호화
- 금융 데이터 접근 기록

## 18. 규제

초기 MVP는 투자정보 분석 및 시뮬레이션 서비스로 제한한다. 실제 투자자문, 투자일임, 주문 실행, 금융상품 판매 등의 기능을 구현할 경우 해당 국가의 금융규제와 라이선스 요구사항을 별도로 검토한다.

AI가 개인에게 특정 금융상품의 매수/매도를 직접 명령하는 구조를 기본값으로 만들지 않는다.

서비스 화면에서도 실제 데이터, 추정 데이터, 시뮬레이션, AI 의견을 명확하게 구분한다.

## 19. 개발 방식

프로젝트를 여러 개발 세션에서 병렬로 개발할 수 있도록 설계한다. 각 세션은 다른 세션의 코드를 임의로 덮어쓰지 않는다.

각 작업은 Task → Implementation → Test → Integration → Result 순서로 진행한다.

각 세션은 작업 종료 시 반드시 다음을 보고한다.

1. 무엇을 구현했는가
2. 어떤 파일을 변경했는가
3. 어떤 테스트를 실행했는가
4. 테스트 결과
5. 아직 남은 문제
6. 다음 세션이 알아야 할 사항

## 20. 첫 단계

아직 코드를 대량으로 작성하지 않는다. 먼저 다음을 작성한다.

```
/docs
  architecture.md
  domain-model.md
  api-contract.md
  data-model.md
  security.md
  regulatory-boundary.md
  roadmap.md
```

그리고 다음을 확정한다.

1. 전체 architecture
2. Domain boundary
3. Database schema
4. API contract
5. Portfolio state model
6. Asset model
7. Transaction model
8. Strategy model
9. Scenario model
10. AI proposal model

그 이후에 MVP 구현을 시작한다.

## 최종 제품 철학

이 프로젝트는 단순한 주식/코인 앱이 아니다. 사용자의 전체 Wealth State를 관찰하고, 데이터를 근거로 위험과 기회를 분석하고, 여러 전략을 시뮬레이션하고, 사용자가 더 나은 금융 의사결정을 할 수 있도록 돕는 Personal Wealth Operating System을 만든다.

핵심 루프는 다음이다: Observe → Normalize → State → Analyze → Simulate → Strategy → Policy → User Decision → Outcome → Feedback → Updated State. 이 루프가 서비스의 핵심 architecture다.

## 사용자 운영 지시

이 프롬프트를 첫 번째 아키텍처 세션에 넣고, 바로 코딩시키기보다 먼저 architecture.md / domain-model.md / data-model.md를 확정하게 한다. 이후 3~5개 세션으로 Frontend / Core Backend / Data & Strategy / AI / Infrastructure를 병렬 분리한다.
