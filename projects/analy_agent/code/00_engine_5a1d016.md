# 00 · 출발점 엔진 해설 (analy_agent `5a1d016`, 브랜치 `claude/great-mccarthy-3lgfqq`)

대상: `trip_optimizer/engine/` 전체 7개 파일, 827줄. 이 문서의 원문 코드 블록은 커밋 `5a1d016`의 파일을 그대로 옮긴 것이다
(손으로 다시 친 것이 아니다). 스펙 근거는 `trip_optimizer/SPEC.md` 3장(핵심 알고리즘), 4.1절(C 인터페이스), 5장(검증)이다.

## 1. 요약과 파일 지도

이 엔진은 "여러 도시를 도는 여행에서 **방문 순서**, **도시별 박수**, **구간별 이동 수단**, **출발일**을 한꺼번에 골라 총비용을
최소화하는" 문제를 푼다. 이동 가격과 숙박 가격은 날짜마다 다르고(시간 의존 비용), 목적 함수는 `구간 가격 합 + 숙박비 합 +
(분당 시간 가치) × 이동 분 합`이다. 방법은 상태를 `(방문한 도시 집합, 현재 도시, 도착일)`로 잡는 동적 계획법(Held-Karp의 시간 의존
확장)이고, 상태마다 최선 1개가 아니라 상위 K개 부분 여정을 들고 다녀서 전체 상위 K개 여정을 돌려준다(K-best DP). 모든 금액·시간은
정수(`int64_t`, `int32_t`)로 계산하고, WebAssembly에서 부르기 위한 평탄화 배열 C 인터페이스가 붙어 있다. 시험은 엔진과 코드를
공유하지 않는 완전 탐색 오라클과 무작위 문제 3000개를 비교하는 것이 중심이다.

| 파일 | 줄 수 | 역할 |
|---|---:|---|
| `CMakeLists.txt` | 28 | 정적 라이브러리 `trip_engine` + GoogleTest 시험 실행 파일 `trip_tests` 빌드. 엔진에만 경고=오류 |
| `include/trip/optimizer.hpp` | 81 | 데이터 모델(`Problem`, `Leg`, `Stay`, `Plan`)과 공개 함수 3개(`validate`, `optimize`, `evaluate`) |
| `include/trip/c_api.h` | 37 | WASM/FFI용 C 함수 3개 선언과 출력 배열 배치 설명 |
| `src/optimizer.cpp` | 263 | K-best DP 본체(`Solver`), 입력 검증, 목적값 재계산 |
| `src/c_api.cpp` | 102 | double 배열 → `Problem` 변환·검사, 결과를 double 배열로 평탄화. 예외 대신 오류 코드 |
| `tests/brute_force.hpp` | 64 | 시험용 완전 탐색 오라클 (순열 × 출발일 × 박수 × 수단을 전부 나열) |
| `tests/test_optimizer.cpp` | 252 | 시험 10개: 손으로 만든 사례 5, 성질 시험 2, 성능 1, C 인터페이스 2 |
| 합계 | 827 | |

## 2. 손 코딩 순서

빈 폴더에서 다시 칠 때 추천하는 순서다. 각 단계는 "빌드가 되고, 그 단계까지의 시험이 녹색"인 상태로 끝낸다.
명령은 저장소 루트(`analy_agent/`) 기준이고, 빌드 폴더는 `build`라고 가정한다.

| 단계 | 칠 것 | 확인 방법 |
|---|---|---|
| 0 | `CMakeLists.txt`. 이 단계에서는 `src/c_api.cpp`를 빈 파일로 만들어 둔다(목록에 있으므로 파일이 없으면 configure가 실패한다) | `cmake -S trip_optimizer/engine -B build -DCMAKE_BUILD_TYPE=Release`가 GoogleTest를 받아 오고 끝나는지 |
| 1 | `optimizer.hpp` 전체 + `optimizer.cpp`의 `validate`, `evaluate`, 그리고 `optimize`는 검증 후 빈 벡터를 돌려주는 임시 버전 | 시험 파일에 `empty_problem`, `set_leg`와 `RejectsMalformedInput`만 넣고 `cmake --build build && ctest --test-dir build -R Rejects` |
| 2 | `tests/brute_force.hpp` (오라클) | 임시 시험 하나: 아래 3.7절의 24가지 순서 예제(`FindsTheOnlyCheapOrderAmong24`의 문제)에서 `oracle::all_costs(p)[0] == 250`. (이 문서를 쓰며 직접 돌려 본 값: 오라클이 여정 96개를 나열하고 가장 싼 셋이 250, 1000, 1000) |
| 3 | `Solver`의 생성자, `run`, `expand`, `leg_cost`, `lodging`, 인덱스 도우미. 처음에는 `push_bounded`/`keep_best`를 "정렬 후 앞 k개" 단순 버전으로, `rebuild`는 `objective`만 채운 `Plan`을 돌려주는 임시 버전으로 | 계획 내용은 아직 비어 있으므로 임시 시험에서 `optimize(p, 1)[0].objective`만 오라클 `all_costs(p)[0]`과 비교 (무작위 문제 몇백 개) |
| 4 | `rebuild`, `add_leg`, `add_stay` | 시험 파일에 `expect_valid_plan`과 손 사례 5개 추가 → `ctest --test-dir build -R '^Optimizer\.'` |
| 5 | K-best 완성: `Entry`/`Final`의 결정적 비교 함수(`better`, `better_final`), 상한 있는 삽입 `push_bounded` | `MatchesBruteForceOnRandomProblems`, `SameInputSameOutput` 추가 → `ctest --test-dir build -R OptimizerProperty` |
| 6 | `c_api.h`, `c_api.cpp` | `CApi.*` 시험 2개 추가 → `ctest --test-dir build -R CApi` |
| 7 | 성능 시험 | `./build/trip_tests --gtest_filter='OptimizerPerformance.*'`로 `[perf]` 줄 확인. 마지막에 `ctest --test-dir build --output-on-failure`로 10/10 |

왜 이 순서인가:
- 데이터 모델과 `validate`가 먼저 있어야 오라클과 DP가 같은 입력을 읽는다.
- 오라클을 DP보다 **먼저** 치는 이유: DP를 먼저 짜면 DP의 답을 보고 오라클을 "맞춰" 쓰게 되기 쉽다. 정답 기준을 먼저 세운다.
- K=1로 먼저 맞추고 K-best로 넓히면, 틀렸을 때 "DP 자체의 버그"인지 "상위 K 병합 버그"인지 나눌 수 있다.
- C 인터페이스는 C++ API를 감싸기만 하므로 C++ 쪽이 시험을 통과한 뒤에 붙인다. `CApi.MatchesCppApiOnRandomProblems`가 C++ API의 결과를 정답으로 쓰기 때문이다.

## 3. 파일별 원문과 해설

손 코딩 순서대로 놓았다: `CMakeLists.txt` → `optimizer.hpp` → `brute_force.hpp` → `optimizer.cpp` → `c_api.h` → `c_api.cpp` → `test_optimizer.cpp`.

### 3.1 `trip_optimizer/engine/CMakeLists.txt` (28줄)

```cmake
cmake_minimum_required(VERSION 3.20)
project(trip_engine CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

option(TRIP_BUILD_TESTS "Build native tests" ON)

add_library(trip_engine STATIC src/optimizer.cpp src/c_api.cpp)
target_include_directories(trip_engine PUBLIC include)
target_compile_options(trip_engine PRIVATE -Wall -Wextra -Werror -Wconversion -Wshadow)

if(TRIP_BUILD_TESTS AND NOT EMSCRIPTEN)
  include(FetchContent)
  FetchContent_Declare(googletest
    GIT_REPOSITORY https://github.com/google/googletest.git
    GIT_TAG v1.15.2
    GIT_SHALLOW TRUE)
  set(INSTALL_GTEST OFF CACHE BOOL "" FORCE)
  FetchContent_MakeAvailable(googletest)

  enable_testing()
  add_executable(trip_tests tests/test_optimizer.cpp)
  target_link_libraries(trip_tests PRIVATE trip_engine GTest::gtest_main)
  include(GoogleTest)
  gtest_discover_tests(trip_tests)
endif()
```

해설:

| 줄 | 무엇 | 왜 |
|---|---|---|
| 1–2 | CMake 3.20 이상, 언어는 C++만(`CXX`) | C 헤더(`c_api.h`)가 있어도 컴파일되는 `.cpp`뿐이라 C 컴파일러가 필요 없다 |
| 4–6 | C++17, 필수, GNU 확장 끔(`-std=c++17`이지 `-std=gnu++17`이 아님) | 네이티브와 Emscripten에서 같은 표준 규칙으로 컴파일되게 |
| 8 | `TRIP_BUILD_TESTS` 옵션, 기본 ON | 라이브러리만 필요할 때 시험을 끌 수 있게 |
| 10 | 정적 라이브러리에 `optimizer.cpp`, `c_api.cpp` | 시험 실행 파일과 (나중의) WASM 빌드가 같은 라이브러리를 링크 |
| 11 | `include`를 PUBLIC으로 | 라이브러리를 링크하는 쪽(시험)도 `#include "trip/optimizer.hpp"`를 쓸 수 있다 |
| 12 | `-Wall -Wextra -Werror -Wconversion -Wshadow`를 **PRIVATE**로 | 엔진 소스에만 적용되고 시험 코드에는 적용되지 않는다. `-Wconversion` 때문에 엔진 코드에는 `static_cast`가 많다(3.4절 참고) |
| 14 | `NOT EMSCRIPTEN`일 때만 시험 | Emscripten으로 빌드할 때는 GoogleTest를 받지 않는다 |
| 15–21 | FetchContent로 GoogleTest `v1.15.2`를 얕은 클론, `INSTALL_GTEST OFF` | 시스템에 GoogleTest가 없어도 빌드된다. 처음 configure할 때 네트워크가 필요하다 |
| 23–27 | `enable_testing`, 실행 파일 `trip_tests`, `GTest::gtest_main` 링크, `gtest_discover_tests` | `gtest_main`이 `main()`을 제공한다. `gtest_discover_tests`가 `TEST(...)` 하나하나를 ctest 시험으로 등록해서 ctest에 10개가 보인다 |

### 3.2 `trip_optimizer/engine/include/trip/optimizer.hpp` (81줄)

```cpp
// Trip optimizer: chooses the visiting order, nights per city, and transport mode
// per leg that minimise the total cost of a multi-city trip, where transport and
// lodging prices depend on the date.
//
// Nodes: 0 = origin, 1..visits = cities to visit (each exactly once),
// visits + 1 = return city (may be the same place as the origin; the engine does
// not care). Days are indices into the planning window [0, days).
//
// All money and time values are integers so that results are exact and identical
// on every platform (native and WebAssembly).
#pragma once

#include <cstdint>
#include <string>
#include <vector>

namespace trip {

struct Problem {
    int visits = 0;  // number of cities to visit
    int days = 0;    // length of the planning window
    int modes = 1;   // transport modes per leg (e.g. flight, train)

    // price[a][b][day][mode] and minutes[a][b][day][mode], flattened with
    // index(a, b, day, mode). A negative price means "no such option".
    std::vector<int64_t> price;
    std::vector<int32_t> minutes;

    // lodging[city][day]: price of the night starting on `day` in `city`.
    // Only rows 1..visits are used. Must be >= 0.
    std::vector<int64_t> lodging;

    std::vector<int32_t> stay_min;  // nights per city, indexed by node (1..visits)
    std::vector<int32_t> stay_max;

    int depart_min = 0;  // earliest / latest day to leave the origin
    int depart_max = 0;

    // "Value for money" weight: cost of one minute of travel time. 0 = cheapest only.
    int64_t cost_per_minute = 0;

    int nodes() const { return visits + 2; }
    size_t index(int a, int b, int day, int mode) const {
        return ((static_cast<size_t>(a) * static_cast<size_t>(nodes()) + static_cast<size_t>(b)) *
                    static_cast<size_t>(days) + static_cast<size_t>(day)) *
                   static_cast<size_t>(modes) + static_cast<size_t>(mode);
    }
};

struct Leg {
    int from, to, day, mode;
    int64_t price;
    int32_t minutes;
};

struct Stay {
    int city, arrive_day, nights;
    int64_t lodging;
};

struct Plan {
    int64_t objective = 0;  // price + lodging + cost_per_minute * minutes
    int64_t transport_price = 0;
    int64_t lodging_price = 0;
    int64_t travel_minutes = 0;
    std::vector<Leg> legs;    // visits + 1 legs, in travel order
    std::vector<Stay> stays;  // one per visited city, in travel order
};

// Returns an empty string if the problem is well formed, else what is wrong.
std::string validate(const Problem& p);

// The k cheapest itineraries by objective, cheapest first. Fewer than k if fewer
// exist; empty if none is feasible. Throws std::invalid_argument on a malformed
// problem. Supports up to 10 cities to visit (the state table grows as 2^visits).
std::vector<Plan> optimize(const Problem& p, int k);

// Recomputes a plan's objective from the problem data; used to check plans.
int64_t evaluate(const Problem& p, const Plan& plan);

}  // namespace trip
```

해설:

- **노드 번호(5–7줄, 42줄).** 0 = 출발 도시, 1..visits = 방문 도시, visits+1 = 귀국 도시. 그래서 노드 수 `nodes() = visits + 2`.
  출발과 귀국이 실제로 같은 도시여도 엔진에서는 다른 노드다(SPEC 3.1). 이렇게 하면 "마지막 구간은 항상 visits+1로 간다"는 규칙
  하나로 끝나서 귀국 처리 분기가 단순해진다.
- **왜 정수인가(9–10줄).** 금액은 `int64_t`, 분은 `int32_t`. 부동소수 덧셈은 순서에 따라 결과가 달라질 수 있어서, 네이티브와 WASM의
  결과를 한 칸씩 비교하려면(SPEC V4) 정수가 안전하다. "원 단위 정수"면 반올림 문제도 없다.
- **`price`, `minutes`의 평탄화(24–27줄, 43–47줄).** 4차원 `price[a][b][day][mode]`를 1차원 벡터에 넣고, 위치는
  `index(a, b, day, mode) = ((a × N + b) × D + day) × M + mode` (N = nodes(), D = days, M = modes). 맨 오른쪽 차원(mode)이 가장 빨리
  변하는 행 우선 배치다. 이 식은 SPEC 4.1과 같은 식이라서, JS가 같은 식으로 배열을 채워 WASM에 그대로 넘길 수 있다.
  - 식 안에서 피연산자마다 먼저 `size_t`로 바꾼 뒤 곱한다. `int`끼리 곱한 다음에 넓히면 중간 곱이 `int` 범위를 넘을 수 있기 때문이다.
  - 크기는 N² × D × M. 예: 방문 8, 기간 30, 수단 3이면 10 × 10 × 30 × 3 = 9,000칸.
  - **가격이 음수면 "그 날 그 수단은 없음"**(25줄). 별도 불리언 배열 없이 한 배열로 표현한다.
- **`lodging`(29–31줄).** `lodging[city][day]` = 그 도시에서 `day`에 시작하는 1박 가격, 평탄화 위치 `city × days + day`. 크기는
  nodes × days지만 1..visits 행만 쓴다(0행과 visits+1행은 자리만 차지한다). 노드 번호를 그대로 행 번호로 쓰려는 선택이다.
- **`stay_min`, `stay_max`(33–34줄).** 노드 번호로 인덱스, 길이 nodes. 0박도 허용된다(`validate`는 `lo < 0`만 거부한다). 0박이면 도착한
  날 바로 떠난다.
- **출발 가능 기간(36–37줄)**: 출발 도시를 떠나는 첫 구간의 날짜 범위. **`cost_per_minute`(40줄)**: 가성비 모드의 가중치.
  0이면 가격만 본다. 단위가 "분당 원"인 정수라서 UI가 "1시간의 가치"를 분 단위로 반올림해 넘긴다(SPEC 3.1).
- **결과 구조(50–68줄).** `Leg`는 구간 하나(출발·도착 노드, 날짜, 수단, 그 구간의 원래 가격과 분), `Stay`는 체류 하나(도시, 도착일,
  박수, 숙박비 합). `Plan`은 목적값과 그 분해(교통비, 숙박비, 이동 분)와 구간 visits+1개, 체류 visits개를 여행 순서대로 담는다.
  `objective = transport_price + lodging_price + cost_per_minute × travel_minutes`가 항상 성립해야 하고, 시험이 이를 검사한다.
- **공개 함수(70–79줄).** `validate`는 문제가 없으면 빈 문자열, 있으면 이유를 돌려준다(예외 없음). `optimize`는 잘못된 입력에
  `std::invalid_argument`를 던진다. `evaluate`는 계획을 문제 데이터로 다시 계산해서, DP가 낸 목적값을 독립적으로 확인하는 데 쓴다.
  `validate`가 예외 없이 따로 공개된 이유는 3.6절(C 인터페이스)에서 나온다.

### 3.3 `trip_optimizer/engine/tests/brute_force.hpp` (64줄)

```cpp
// Test oracle: enumerate every itinerary (order x departure day x nights x modes)
// and return all objective values. Deliberately written differently from the
// optimizer (plain recursion, no shared helpers) so that a bug in one is unlikely
// to be repeated in the other.
#pragma once

#include <algorithm>
#include <cstdint>
#include <vector>

#include "trip/optimizer.hpp"

namespace oracle {

inline int64_t leg(const trip::Problem& p, int a, int b, int d, int m, bool& ok) {
    const int64_t price = p.price[p.index(a, b, d, m)];
    if (price < 0) {
        ok = false;
        return 0;
    }
    return price + p.cost_per_minute * p.minutes[p.index(a, b, d, m)];
}

inline void walk(const trip::Problem& p, std::vector<int>& order, size_t pos, int city, int arrive, int64_t cost,
                 std::vector<int64_t>& out) {
    const int nodes = p.visits + 2;
    for (int s = p.stay_min[static_cast<size_t>(city)]; s <= p.stay_max[static_cast<size_t>(city)]; s++) {
        const int depart = arrive + s;
        if (depart >= p.days) break;
        int64_t lodge = 0;
        for (int d = arrive; d < depart; d++) lodge += p.lodging[static_cast<size_t>(city * p.days + d)];
        const int next = pos + 1 < order.size() ? order[pos + 1] : nodes - 1;
        for (int m = 0; m < p.modes; m++) {
            bool ok = true;
            const int64_t c = leg(p, city, next, depart, m, ok);
            if (!ok) continue;
            if (next == nodes - 1) {
                out.push_back(cost + lodge + c);
            } else {
                walk(p, order, pos + 1, next, depart, cost + lodge + c, out);
            }
        }
    }
}

// All feasible objective values, sorted ascending.
inline std::vector<int64_t> all_costs(const trip::Problem& p) {
    std::vector<int> order;
    for (int c = 1; c <= p.visits; c++) order.push_back(c);
    std::vector<int64_t> out;
    do {
        for (int d0 = p.depart_min; d0 <= p.depart_max; d0++) {
            for (int m = 0; m < p.modes; m++) {
                bool ok = true;
                const int64_t c = leg(p, 0, order[0], d0, m, ok);
                if (ok) walk(p, order, 0, order[0], d0, c, out);
            }
        }
    } while (std::next_permutation(order.begin(), order.end()));
    std::sort(out.begin(), out.end());
    return out;
}

}  // namespace oracle
```

해설:

- **역할.** 가능한 모든 여정을 나열해 목적값을 전부 모은다. 엔진의 상위 K개 목적값은 이 목록을 정렬한 앞 K개와 같아야 한다(SPEC V1).
- **일부러 다르게 썼다(1–4줄).** DP도, 누적합도, 엔진의 도우미 함수도 쓰지 않는다. 공유하는 것은 `trip::Problem`과
  `Problem::index` 뿐이다. 같은 실수가 양쪽에 똑같이 들어가면 비교 시험이 그 버그를 못 잡기 때문이다.
  - 숙박비는 누적합이 아니라 반복문으로 더한다(31줄). 인덱스도 `int` 산술(`city * p.days + d`)로 직접 계산한다.
- **`all_costs`(47–62줄).** 방문 도시 1..V의 순열을 `std::next_permutation`으로 모두 돈다(처음 순서가 정렬돼 있어야 모든 순열이
  나온다. 49줄이 1, 2, …, V로 채운다). 각 순열마다 출발일 `d0`(depart_min..depart_max) × 첫 구간 수단 `m`을 고르고, 첫 구간이
  있으면 `walk`로 내려간다. 마지막에 정렬해서 오름차순으로 돌려준다. 같은 값이 여러 번 나와도 지우지 않는다. 엔진도 서로 다른 여정
  K개를 돌려주므로, 동점까지 포함한 "다중집합"의 앞 K개를 비교해야 맞다.
- **`walk`(24–44줄).** 지금 `city`에 `arrive`일에 도착한 상태에서 박수 `s`를 stay_min..stay_max로 고르고, 떠나는 날
  `depart = arrive + s`가 기간 밖(`>= p.days`)이면 `break`. 다음 노드는 순열의 다음 도시, 순열이 끝났으면 귀국 노드(`nodes - 1`, 32줄).
  수단마다 구간이 있으면 귀국이면 결과에 넣고(38줄), 아니면 재귀(40줄).
- **`leg`(15–22줄).** 가격이 음수면 `ok = false`. 비용은 `가격 + cost_per_minute × 분`.
- **계산량.** V! × (출발일 수) × (박수 선택지)^V × M^(V+1) 정도다. 그래서 무작위 시험은 V ≤ 4, D ≤ 8로 작게 잡는다(3.7절).

### 3.4 `trip_optimizer/engine/src/optimizer.cpp` (263줄)

```cpp
// Dynamic programming over (set of visited cities, current city, arrival day).
//
// A state's value is the cost of reaching `city` on `day` having visited exactly
// `mask`. From a state we choose the number of nights s (within the city's stay
// range), depart on day + s, and pick the next unvisited city (or the return city
// once all are visited) and a transport mode. Costs are additive, so keeping the
// k best partial itineraries per state is enough to recover the k best complete
// ones (k-best dynamic programming).
#include "trip/optimizer.hpp"

#include <algorithm>
#include <stdexcept>

namespace trip {
namespace {

struct Entry {
    int64_t cost;
    int prev_state;  // -1: the leg starts at the origin
    int prev_rank;
    int nights;      // nights spent in the previous city (0 when leaving the origin)
    int day;         // departure day of the leg into this state
    int mode;
};

struct Final {
    int64_t cost;
    int state, rank, nights, day, mode;
};

bool better(const Entry& a, const Entry& b) {
    // Deterministic order: cost first, then the choice that produced the entry.
    if (a.cost != b.cost) return a.cost < b.cost;
    if (a.prev_state != b.prev_state) return a.prev_state < b.prev_state;
    if (a.prev_rank != b.prev_rank) return a.prev_rank < b.prev_rank;
    if (a.nights != b.nights) return a.nights < b.nights;
    if (a.day != b.day) return a.day < b.day;
    return a.mode < b.mode;
}

bool better_final(const Final& a, const Final& b) {
    if (a.cost != b.cost) return a.cost < b.cost;
    if (a.state != b.state) return a.state < b.state;
    if (a.rank != b.rank) return a.rank < b.rank;
    if (a.nights != b.nights) return a.nights < b.nights;
    if (a.day != b.day) return a.day < b.day;
    return a.mode < b.mode;
}

template <typename T, typename Less>
void keep_best(std::vector<T>& v, size_t k, Less less) {
    std::sort(v.begin(), v.end(), less);
    if (v.size() > k) v.resize(k);
}

// Bounded insert: keep the list from growing far beyond k between trims.
template <typename T, typename Less>
void push_bounded(std::vector<T>& v, const T& x, size_t k, Less less) {
    v.push_back(x);
    if (v.size() > 4 * k) {
        std::nth_element(v.begin(), v.begin() + static_cast<long>(k) - 1, v.end(), less);
        v.resize(k);
    }
}

class Solver {
public:
    Solver(const Problem& p, int k) : p_(p), k_(static_cast<size_t>(k)) {
        lodging_prefix_.assign(static_cast<size_t>(p.nodes()) * static_cast<size_t>(p.days + 1), 0);
        for (int c = 1; c <= p.visits; c++) {
            for (int d = 0; d < p.days; d++) {
                lodging_prefix_[pidx(c, d + 1)] = lodging_prefix_[pidx(c, d)] + p.lodging[lidx(c, d)];
            }
        }
        states_.resize((size_t{1} << p.visits) * static_cast<size_t>(p.visits) * static_cast<size_t>(p.days));
    }

    std::vector<Plan> run() {
        const int full = (1 << p_.visits) - 1;

        // First leg: origin -> city j.
        for (int d = p_.depart_min; d <= p_.depart_max; d++) {
            for (int j = 1; j <= p_.visits; j++) {
                for (int m = 0; m < p_.modes; m++) {
                    int64_t c;
                    if (!leg_cost(0, j, d, m, c)) continue;
                    push_bounded(states_[sidx(1 << (j - 1), j, d)], Entry{c, -1, 0, 0, d, m}, k_, better);
                }
            }
        }

        std::vector<Final> finals;
        for (int mask = 1; mask <= full; mask++) {
            for (int i = 1; i <= p_.visits; i++) {
                if (!(mask & (1 << (i - 1)))) continue;
                for (int t = 0; t < p_.days; t++) {
                    const int s_index = sidx(mask, i, t);
                    std::vector<Entry>& here = states_[static_cast<size_t>(s_index)];
                    if (here.empty()) continue;
                    keep_best(here, k_, better);
                    expand(mask, i, t, s_index, full, finals);
                }
            }
        }

        keep_best(finals, k_, better_final);
        std::vector<Plan> plans;
        for (const Final& f : finals) plans.push_back(rebuild(f));
        return plans;
    }

private:
    void expand(int mask, int i, int t, int s_index, int full, std::vector<Final>& finals) {
        const std::vector<Entry>& here = states_[static_cast<size_t>(s_index)];
        for (int s = p_.stay_min[static_cast<size_t>(i)]; s <= p_.stay_max[static_cast<size_t>(i)]; s++) {
            const int d = t + s;
            if (d >= p_.days) break;
            const int64_t lodge = lodging(i, t, s);
            if (mask == full) {
                const int ret = p_.visits + 1;
                for (int m = 0; m < p_.modes; m++) {
                    int64_t c;
                    if (!leg_cost(i, ret, d, m, c)) continue;
                    for (size_t r = 0; r < here.size(); r++) {
                        push_bounded(finals, Final{here[r].cost + lodge + c, s_index, static_cast<int>(r), s, d, m},
                                     k_, better_final);
                    }
                }
                continue;
            }
            for (int j = 1; j <= p_.visits; j++) {
                if (mask & (1 << (j - 1))) continue;
                for (int m = 0; m < p_.modes; m++) {
                    int64_t c;
                    if (!leg_cost(i, j, d, m, c)) continue;
                    std::vector<Entry>& next = states_[static_cast<size_t>(sidx(mask | (1 << (j - 1)), j, d))];
                    for (size_t r = 0; r < here.size(); r++) {
                        push_bounded(next, Entry{here[r].cost + lodge + c, s_index, static_cast<int>(r), s, d, m},
                                     k_, better);
                    }
                }
            }
        }
    }

    Plan rebuild(const Final& f) const {
        Plan plan;
        plan.objective = f.cost;
        // Walk back from the final leg, collecting legs and stays in reverse.
        int state = f.state, rank = f.rank, nights = f.nights, day = f.day, mode = f.mode;
        int to = p_.visits + 1;
        while (true) {
            const int city = city_of(state);
            const int arrive = day_of(state);
            add_leg(plan, city, to, day, mode);
            add_stay(plan, city, arrive, nights);
            const Entry& e = states_[static_cast<size_t>(state)][static_cast<size_t>(rank)];
            to = city;
            if (e.prev_state < 0) {
                add_leg(plan, 0, to, e.day, e.mode);
                break;
            }
            state = e.prev_state;
            rank = e.prev_rank;
            nights = e.nights;
            day = e.day;
            mode = e.mode;
        }
        std::reverse(plan.legs.begin(), plan.legs.end());
        std::reverse(plan.stays.begin(), plan.stays.end());
        return plan;
    }

    void add_leg(Plan& plan, int from, int to, int day, int mode) const {
        const size_t x = p_.index(from, to, day, mode);
        plan.legs.push_back(Leg{from, to, day, mode, p_.price[x], p_.minutes[x]});
        plan.transport_price += p_.price[x];
        plan.travel_minutes += p_.minutes[x];
    }

    void add_stay(Plan& plan, int city, int arrive, int nights) const {
        const int64_t l = lodging(city, arrive, nights);
        plan.stays.push_back(Stay{city, arrive, nights, l});
        plan.lodging_price += l;
    }

    bool leg_cost(int a, int b, int d, int m, int64_t& out) const {
        const size_t x = p_.index(a, b, d, m);
        if (p_.price[x] < 0) return false;
        out = p_.price[x] + p_.cost_per_minute * p_.minutes[x];
        return true;
    }

    int64_t lodging(int city, int arrive, int nights) const {
        return lodging_prefix_[pidx(city, arrive + nights)] - lodging_prefix_[pidx(city, arrive)];
    }

    int sidx(int mask, int city, int day) const {
        return (mask * p_.visits + (city - 1)) * p_.days + day;
    }
    int city_of(int s) const { return (s / p_.days) % p_.visits + 1; }
    int day_of(int s) const { return s % p_.days; }
    size_t pidx(int c, int d) const { return static_cast<size_t>(c) * static_cast<size_t>(p_.days + 1) + static_cast<size_t>(d); }
    size_t lidx(int c, int d) const { return static_cast<size_t>(c) * static_cast<size_t>(p_.days) + static_cast<size_t>(d); }

    const Problem& p_;
    size_t k_;
    std::vector<int64_t> lodging_prefix_;
    std::vector<std::vector<Entry>> states_;
};

}  // namespace

std::string validate(const Problem& p) {
    if (p.visits < 1 || p.visits > 10) return "visits must be between 1 and 10";
    if (p.days < 1) return "days must be at least 1";
    if (p.modes < 1) return "modes must be at least 1";
    const size_t legs = static_cast<size_t>(p.nodes()) * static_cast<size_t>(p.nodes()) *
                        static_cast<size_t>(p.days) * static_cast<size_t>(p.modes);
    if (p.price.size() != legs || p.minutes.size() != legs) return "price/minutes size mismatch";
    if (p.lodging.size() != static_cast<size_t>(p.nodes()) * static_cast<size_t>(p.days)) return "lodging size mismatch";
    if (p.stay_min.size() != static_cast<size_t>(p.nodes()) || p.stay_max.size() != static_cast<size_t>(p.nodes())) {
        return "stay range size mismatch";
    }
    for (int c = 1; c <= p.visits; c++) {
        const int lo = p.stay_min[static_cast<size_t>(c)], hi = p.stay_max[static_cast<size_t>(c)];
        if (lo < 0 || hi < lo) return "invalid stay range for city " + std::to_string(c);
        for (int d = 0; d < p.days; d++) {
            if (p.lodging[static_cast<size_t>(c) * static_cast<size_t>(p.days) + static_cast<size_t>(d)] < 0) {
                return "lodging prices must be >= 0";
            }
        }
    }
    for (int32_t m : p.minutes) {
        if (m < 0) return "minutes must be >= 0";
    }
    if (p.depart_min < 0 || p.depart_max < p.depart_min || p.depart_max >= p.days) return "invalid departure window";
    if (p.cost_per_minute < 0) return "cost_per_minute must be >= 0";
    return "";
}

std::vector<Plan> optimize(const Problem& p, int k) {
    const std::string err = validate(p);
    if (!err.empty()) throw std::invalid_argument(err);
    if (k < 1) throw std::invalid_argument("k must be at least 1");
    return Solver(p, k).run();
}

int64_t evaluate(const Problem& p, const Plan& plan) {
    int64_t total = 0;
    for (const Leg& l : plan.legs) {
        const size_t x = p.index(l.from, l.to, l.day, l.mode);
        total += p.price[x] + p.cost_per_minute * p.minutes[x];
    }
    for (const Stay& s : plan.stays) {
        for (int d = s.arrive_day; d < s.arrive_day + s.nights; d++) {
            total += p.lodging[static_cast<size_t>(s.city) * static_cast<size_t>(p.days) + static_cast<size_t>(d)];
        }
    }
    return total;
}

}  // namespace trip
```

해설:

**(1) 상태 정의와 점화식 (1–8줄 주석, 198–202줄).**
- 상태 = `(mask, city, day)`: 방문한 도시 집합이 비트마스크 `mask`(도시 j는 비트 j−1), 지금 도시 `city`(1..V), 그 도시에 **도착한 날** `day`.
- 값 = 출발 도시에서 시작해 그 상태에 이르는 부분 여정의 비용들 중 상위 K개 (`std::vector<Entry>`).
- 전이: 상태 `(mask, i, t)`에서 박수 `s`를 고르면 떠나는 날 `d = t + s`. 다음 도시 `j`(아직 안 간 도시)와 수단 `m`을 골라
  `(mask | bit(j), j, d)`로 간다. 비용 증가 = `lodging(i, t, s) + price + cost_per_minute × minutes`. 구간은 떠난 날 도착한다(SPEC 3.1),
  그래서 다음 상태의 도착일도 `d`다.
- 모든 도시를 방문한 상태(`mask == full`)에서는 다음 도시 대신 귀국 노드 visits+1로 가는 구간을 붙여 완성 여정(`Final`)이 된다.
- 상태 번호 `sidx(mask, city, day) = (mask × V + (city − 1)) × D + day`(198–200줄). 거꾸로 `day_of = s % D`, `city_of = (s / D) % V + 1`
  (201–202줄). 상태 표 크기는 `2^V × V × D`(75줄). mask 0 칸은 쓰지 않지만 식을 단순하게 하려고 그대로 둔다.
  예: V = 8, D = 30이면 256 × 8 × 30 = 61,440칸.

**(2) `Entry`와 `Final` (17–29줄): 역추적용 정보.**
- `Entry`는 "이 상태로 들어온 한 가지 방법"이다. 비용, 이전 상태 번호 `prev_state`(출발 도시에서 왔으면 −1), 이전 상태 목록에서의
  순위 `prev_rank`, **이전 도시에서** 묵은 박수 `nights`, 이 상태로 들어온 구간의 출발일 `day`와 수단 `mode`.
- 도시 i의 박수는 i를 **떠날 때**(`expand`에서) 정해진다. 그래서 i의 박수는 i의 상태가 아니라 다음 상태의 `Entry`(마지막 도시라면
  `Final`)에 적힌다. 첫 구간 `Entry`의 `nights`가 0인 이유는 출발 도시에는 체류가 없기 때문이다(21줄 주석).
- `Final`은 완성 여정 하나: 비용, 마지막 도시의 상태 번호 `state`와 그 안의 순위 `rank`, 마지막 도시 박수, 귀국 구간의 날짜·수단.
- 경로 전체를 복사해 들고 다니지 않고 "이전 칸 + 순위" 포인터만 저장한다. 그래서 상태당 메모리가 K × (Entry 크기)로 일정하다.

**(3) 결정적 순서 `better`, `better_final` (31–48줄).**
- 비용이 같으면 `prev_state`, `prev_rank`, `nights`, `day`, `mode` 순서로 비교한다. 한 목표 상태 안에서 이 다섯 값이 모두 같은
  `Entry`는 같은 선택이므로, 이 비교는 서로 다른 원소 사이에 항상 우열을 정하는 **전순서**다.
- 전순서가 왜 필요한가: `std::sort`와 `std::nth_element`는 안정 정렬이 아니어서, 같다고 판정된 원소들의 순서는 표준이 정하지 않는다.
  전순서면 "앞 K개" 집합과 그 순서가 입력만으로 유일하게 정해진다(SPEC 3.2 "동점 처리"). 표준 라이브러리 구현이 다른 환경
  (네이티브와 Emscripten)에서도 같은 결과를 내려면 이 성질이 필요하다.
- 참고(직접 실험): `better`를 비용만 비교하게 바꿔도 현재 시험 10개는 모두 통과했다. 같은 실행 파일 안에서는 정렬 알고리즘이
  같아서 `SameInputSameOutput`이 차이를 볼 수 없기 때문이다. 이 결함은 서로 다른 빌드를 비교하는 V4 같은 시험이 있어야 드러날 수 있다.

**(4) 상위 K개 유지: `keep_best`, `push_bounded` (50–64줄).**
- `keep_best`: 전부 정렬한 뒤 앞 k개만 남긴다. 상태를 **펼치기 직전**(100줄)과 완성 여정 목록을 마무리할 때(106줄) 부른다.
- `push_bounded`: 일단 넣고, 길이가 4k를 넘으면 `nth_element`로 앞 k개(k번째 위치 `begin + k − 1` 기준으로 그보다 작은 것들이 앞에
  모임)만 남기고 자른다. 상태 하나로 들어오는 후보는 (이전 상태 수 × 박수 × 수단 × K)개까지 많아질 수 있는데, 매번 정렬하지 않으면서
  메모리를 k의 상수배로 묶어 두는 장치다. 자를 때 순서는 정렬되지 않지만, 나중에 `keep_best`가 정렬한다.
- 4k 기준은 "자주 자르지 않아 비용을 나누고, 그래도 길이는 한정"하려는 절충이다. 이 상수 자체는 정답에 영향이 없다.
- 61줄의 `static_cast<long>(k) - 1`은 반복자에 더할 부호 있는 정수(차이형)에 맞춘 것이다.

**(5) 왜 상태마다 K개만 남겨도 되는가 (6–8줄 주석).**
- 한 상태 `(mask, city, day)` 이후에 가능한 "남은 여정"과 그 비용은 그 상태에만 달려 있고, 거기까지 어떻게 왔는지와 무관하다.
  비용은 더해지기만 한다.
- 그래서 어떤 완성 여정 P가 전체 상위 K개에 들어가려면, P가 지나간 상태에서 P의 앞부분이 그 상태의 상위 K개 안에 있어야 한다.
  만약 앞부분보다 나은 앞부분이 K개 있다면, 그 각각에 P의 뒷부분을 그대로 붙인 K개의 서로 다른 완성 여정이 P보다 나쁘지 않기
  때문이다. 동점이 있어도 목적값의 "앞 K개 목록"은 보존된다.

**(6) 생성자 (68–76줄): 숙박비 누적합.**
- `lodging_prefix_[pidx(c, d)]` = 도시 c의 0..d−1일 숙박비 합. 행 너비는 `days + 1`(203줄). 그러면
  `lodging(city, arrive, nights) = prefix[arrive + nights] − prefix[arrive]`(194–196줄)로 몇 박이든 O(1)에 구한다.
- `lidx`(204줄)는 원본 `lodging` 배열의 `city × days + day` 위치, `pidx`는 누적합 배열의 위치다. 너비가 하나 달라서 두 함수가 따로 있다.
- `states_`는 `2^V × V × D`개의 빈 벡터로 시작한다(75줄).

**(7) `run` (78–110줄).**
- 81–90줄: 첫 구간. 출발일 d(depart_min..depart_max) × 도시 j × 수단 m에 대해, 구간이 있으면(`leg_cost`가 true) 상태
  `(1 << (j−1), j, d)`에 `Entry{c, -1, 0, 0, d, m}`을 넣는다.
- 93–104줄: mask를 1부터 `full`까지 **정수 오름차순**으로 돈다. 전이는 항상 mask에 비트를 하나 더하므로(값이 커짐), 어떤 상태를
  펼칠 때 그 상태로 들어오는 전이는 이미 모두 끝나 있다. 이것이 처리 순서(위상 순서)의 근거다. 같은 mask 안에서는 서로 전이가
  없으므로 도시·날짜 순서는 상관없다.
- 99줄: 도달하지 못한 상태는 건너뛴다. 100줄: 펼치기 전에 정렬·자르기. 이때 정해진 순위가 다음 상태들의 `prev_rank`가 가리키는
  번호가 되고, 이 목록은 이후 다시 바뀌지 않는다(더 큰 mask에만 쓰기 때문). 그래서 역추적 포인터가 끝까지 유효하다.
- 106–109줄: 완성 여정 목록을 정렬·자르고, 각각을 `rebuild`로 `Plan`으로 바꾼다. 가능한 여정이 K개보다 적으면 그만큼만, 없으면 빈 벡터.

**(8) `expand` (113–144줄).**
- 115줄: 박수 s = stay_min..stay_max (**양 끝 포함** `<=`). 116–117줄: 떠나는 날 `d = t + s`가 기간 밖(`d >= days`)이면 `break`.
  s가 커질수록 d도 커지므로 `continue`가 아니라 `break`다. 이 조건이 SPEC의 `t + s ≤ D − 1`이다.
- 118줄: 숙박비는 박수마다 한 번만 계산한다.
- 119–130줄: 모든 도시를 방문했으면 귀국 노드로 가는 구간만 본다. 지금 상태의 K개 각각(`r`)에 대해 `Final`을 만들어 `finals`에 넣는다.
- 131–142줄: 아니면 안 간 도시 j × 수단 m에 대해, 다음 상태 목록 `next`에 지금 상태의 K개 각각을 이어 붙인 `Entry`를 넣는다.
  이것이 **K-best 병합**이다: 다음 상태 하나에는 여러 이전 상태(이전 도시·도착일·박수·수단이 다른)에서 온 후보들이 모이고,
  `push_bounded`와 나중의 `keep_best`가 그중 앞 K개만 남긴다.
- 계산량: 상태 2^V × V × D개 각각에서 (박수 선택지 S) × (다음 도시 ≤ V) × M × K번 넣기를 하므로 넣기 횟수는 많아야
  2^V × V² × D × S × M × K다(SPEC 3.2의 추정식에 K가 곱해진 꼴). 여기에 정렬 비용이 더해진다. 메모리는 상태 수 × K × Entry.

**(9) `rebuild` (146–172줄): 역추적.**
- `Final`에서 시작한다. 현재 상태 번호에서 도시와 도착일을 꺼내고(153–154줄), "도시 → to" 구간(155줄)과 그 도시의 체류(156줄)를 넣는다.
  처음 `to`는 귀국 노드(151줄).
- 157줄: 지금 상태의 `rank`번째 `Entry`가 "이 도시로 어떻게 왔나"를 알려 준다. `prev_state < 0`이면 출발 도시에서 온 첫 구간을
  넣고 끝(159–162줄). 아니면 이전 상태로 옮기면서, `Entry`에 적힌 `nights`(이전 도시의 박수), `day`(이전 도시를 떠난 날), `mode`를 다음
  반복에 넘긴다(163–167줄).
- 뒤에서부터 모았으므로 마지막에 `legs`와 `stays`를 뒤집는다(169–170줄).
- `objective`는 DP의 비용을 그대로 쓰고(148줄), `transport_price`, `travel_minutes`, `lodging_price`는 `add_leg`, `add_stay`가 문제 데이터에서
  다시 더한다(174–185줄). `Leg.price`에는 시간 가치를 더하지 않은 원래 가격이 들어간다. 그래서 시험의
  `objective == transport + lodging + cpm × minutes` 검사가 DP 비용과 역추적 결과가 서로 맞는지를 확인하는 셈이 된다.

**(10) `validate` (214–240줄)와 `optimize` (242–247줄), `evaluate` (249–261줄).**
- `validate`가 막는 것: visits 1..10, days ≥ 1, modes ≥ 1, 배열 크기 4종, 방문 도시의 박수 범위(`0 ≤ lo ≤ hi`), 방문 도시의 숙박비 ≥ 0,
  모든 분 ≥ 0, 출발 기간 `0 ≤ depart_min ≤ depart_max < days`, cost_per_minute ≥ 0. 가격 음수는 "없음"이라는 뜻이라 막지 않는다.
  stay_max의 상한도 막지 않는다(기간 밖은 `expand`가 `break`로 처리).
- 10개 한도(215줄)는 상태 표가 2^V에 비례해 커지기 때문이다(SPEC 3.2).
- `optimize`는 검증 실패나 k < 1이면 `std::invalid_argument`를 던지고, 아니면 `Solver(p, k).run()`.
- `evaluate`는 `Solver`의 어떤 함수도 쓰지 않고, 구간 비용은 `price + cpm × minutes`, 숙박비는 날짜별 반복으로 다시 더한다.
- 참고: 엔진은 `int64_t` 덧셈·곱셈의 오버플로를 검사하지 않는다. C 인터페이스가 각 값을 2^53 미만으로 제한하지만, 곱
  `cost_per_minute × minutes`의 범위까지 막지는 않는다.

**(11) `static_cast`가 많은 이유.** 엔진은 `-Wconversion -Werror`로 컴파일된다. 이 경고는 값이 바뀔 수 있는 변환(예: `size_t → int`,
`int64_t → double`)에서 나고, 경고가 곧 빌드 실패다. 그래서 `static_cast<int>(r)`(125, 138줄)처럼 좁히는 변환을 모두 명시한다.
(직접 확인: GCC 13에서 `-Wconversion`은 `int64_t → double`과 `size_t → int`는 경고하고, `int → double`과 `int × int → size_t`는
경고하지 않았다. 그래서 인덱스 계산의 `static_cast<size_t>`는 경고 때문이라기보다 곱셈을 `size_t`에서 하려는 목적이 크다.)

### 3.5 `trip_optimizer/engine/include/trip/c_api.h` (37줄)

```c
/*
 * C interface for WebAssembly (and any other FFI).
 *
 * Inputs are flat arrays in the layout of trip::Problem. Money and minutes are
 * passed as doubles because JavaScript numbers are doubles; they must hold whole
 * numbers below 2^53, which is checked, so results stay exact.
 *
 * Output layout, repeated for each plan:
 *   objective, transport_price, lodging_price, travel_minutes,
 *   n_legs,  then n_legs  x (from, to, day, mode, price, minutes),
 *   n_stays, then n_stays x (city, arrive_day, nights, lodging)
 */
#ifndef TRIP_C_API_H
#define TRIP_C_API_H

#ifdef __cplusplus
extern "C" {
#endif

/* Doubles needed in `out` for k plans of a trip with `visits` cities. */
int trip_output_size(int visits, int k);

/* Returns the number of plans written (0 = no feasible trip), or -1 on invalid
 * input (see trip_last_error) or -2 if `out_len` is too small. */
int trip_optimize(int visits, int days, int modes,
                  const double* price, const double* minutes, const double* lodging,
                  const int* stay_min, const int* stay_max,
                  int depart_min, int depart_max, double cost_per_minute,
                  int k, double* out, int out_len);

const char* trip_last_error(void);

#ifdef __cplusplus
}
#endif

#endif /* TRIP_C_API_H */
```

해설:

- **왜 C 인터페이스인가.** Emscripten이 JS에 내보내는 함수는 이름이 맹글링되지 않은 C 함수가 다루기 쉽다. `std::vector`나 구조체 대신
  포인터와 정수만 오가므로 JS 쪽은 WASM 힙에 숫자 배열을 쓰고 포인터만 넘기면 된다. JSON 파서도 필요 없다(SPEC 4.1).
- **`extern "C"` 가드(16–18, 33–35줄).** C++로 컴파일할 때만 `extern "C" { }`로 감싸 C 링크 이름을 쓰게 한다. C 컴파일러에서도
  같은 헤더를 읽을 수 있다. 주석도 `/* */`만 쓴다.
- **출력 배치(8–11줄).** 계획마다 `목적값, 교통비, 숙박비, 이동 분, 구간 수, 구간 × (from, to, day, mode, price, minutes), 체류 수,
  체류 × (city, arrive_day, nights, lodging)`. 길이를 앞에 적는 형식이라 읽는 쪽이 순서대로 해석할 수 있다.
- **반환값(23–24줄).** 쓴 계획 수(0 = 가능한 여행 없음), −1 = 입력 오류(`trip_last_error()`로 이유 조회), −2 = 출력 버퍼 부족.
- `stay_min`, `stay_max`는 `int*`이고 길이는 노드 수(visits + 2)다(c_api.cpp 61–62줄이 그만큼 읽는다).

### 3.6 `trip_optimizer/engine/src/c_api.cpp` (102줄)

```cpp
#include "trip/c_api.h"

#include <cmath>
#include <cstdint>
#include <string>
#include <vector>

#include "trip/optimizer.hpp"

namespace {

std::string g_error;

constexpr double kMaxExact = 9007199254740992.0;  // 2^53

bool to_int64(double v, int64_t& out) {
    if (!std::isfinite(v) || std::floor(v) != v || std::fabs(v) >= kMaxExact) return false;
    out = static_cast<int64_t>(v);
    return true;
}

}  // namespace

extern "C" {

int trip_output_size(int visits, int k) {
    return k * (4 + 1 + 6 * (visits + 1) + 1 + 4 * visits);
}

int trip_optimize(int visits, int days, int modes, const double* price, const double* minutes,
                  const double* lodging, const int* stay_min, const int* stay_max, int depart_min,
                  int depart_max, double cost_per_minute, int k, double* out, int out_len) {
    g_error.clear();
    if (visits < 1 || visits > 10 || days < 1 || modes < 1 || k < 1) {
        g_error = "visits must be 1..10, days, modes and k at least 1";
        return -1;
    }
    trip::Problem p;
    p.visits = visits;
    p.days = days;
    p.modes = modes;
    const size_t nodes = static_cast<size_t>(visits + 2);
    const size_t legs = nodes * nodes * static_cast<size_t>(days) * static_cast<size_t>(modes);
    p.price.resize(legs);
    p.minutes.resize(legs);
    for (size_t i = 0; i < legs; i++) {
        int64_t m;
        if (!to_int64(price[i], p.price[i]) || !to_int64(minutes[i], m) || m > INT32_MAX) {
            g_error = "price and minutes must be whole numbers";
            return -1;
        }
        p.minutes[i] = static_cast<int32_t>(m);
    }
    p.lodging.resize(nodes * static_cast<size_t>(days));
    for (size_t i = 0; i < p.lodging.size(); i++) {
        if (!to_int64(lodging[i], p.lodging[i])) {
            g_error = "lodging prices must be whole numbers";
            return -1;
        }
    }
    p.stay_min.assign(stay_min, stay_min + nodes);
    p.stay_max.assign(stay_max, stay_max + nodes);
    p.depart_min = depart_min;
    p.depart_max = depart_max;
    if (!to_int64(cost_per_minute, p.cost_per_minute)) {
        g_error = "cost per minute must be a whole number";
        return -1;
    }
    if (out_len < trip_output_size(visits, k)) {
        g_error = "output buffer too small";
        return -2;
    }

    // Validate here instead of catching the optimizer's exception: WebAssembly builds
    // disable C++ exception catching by default, so a throw would abort the module.
    g_error = trip::validate(p);
    if (!g_error.empty()) return -1;
    const std::vector<trip::Plan> plans = trip::optimize(p, k);

    size_t w = 0;
    auto put = [&](double v) { out[w++] = v; };
    for (const trip::Plan& plan : plans) {
        put(static_cast<double>(plan.objective));
        put(static_cast<double>(plan.transport_price));
        put(static_cast<double>(plan.lodging_price));
        put(static_cast<double>(plan.travel_minutes));
        put(static_cast<double>(plan.legs.size()));
        for (const trip::Leg& l : plan.legs) {
            put(l.from); put(l.to); put(l.day); put(l.mode);
            put(static_cast<double>(l.price)); put(l.minutes);
        }
        put(static_cast<double>(plan.stays.size()));
        for (const trip::Stay& s : plan.stays) {
            put(s.city); put(s.arrive_day); put(s.nights); put(static_cast<double>(s.lodging));
        }
    }
    return static_cast<int>(plans.size());
}

const char* trip_last_error(void) { return g_error.c_str(); }

}  // extern "C"
```

해설:

- **왜 금액이 `double`로 들어오나(헤더 4–6줄).** JS 숫자는 모두 64비트 double이라 JS 배열을 그대로 `Float64Array`로 넘기기 쉽다.
  double은 절댓값 2^53 이하의 정수를 정확히 표현한다. 그래서 `to_int64`(16–20줄)가 **유한한가, 정수인가(`floor(v) == v`),
  절댓값이 2^53 미만인가**를 검사한 뒤에만 `int64_t`로 바꾼다. 이 검사를 통과한 값은 변환해도 바뀌지 않으므로 이후 계산은 엔진의
  정수 계산 그대로다. 0.5원 같은 값은 반올림하지 않고 거부한다(−1).
- **검사 순서(33–72줄).**
  1. 33줄: 지난 호출의 오류 문자열을 지운다.
  2. 34–37줄: 크기 인자(visits, days, modes, k)를 **배열을 읽기 전에** 검사한다. 배열 길이가 이 값들로 계산되므로, 잘못된 값으로
     배열을 읽으면 범위를 벗어날 수 있다.
  3. 42–53줄: `price`, `minutes`를 변환. 분은 추가로 `INT32_MAX` 이하인지 본다(`int32_t`에 담기 때문). 음수 분은 여기서는 통과하고
     76줄 `validate`가 거부한다.
  4. 54–68줄: 숙박비, 박수 범위(int 그대로 복사), 출발 기간, cost_per_minute.
  5. 69–72줄: 출력 버퍼가 `trip_output_size(visits, k)`보다 작으면 −2.
  6. 74–77줄: `trip::validate`로 검증하고 실패면 −1.
- **왜 예외를 쓰지 않나(74–75줄 주석).** Emscripten 빌드는 기본 설정에서 C++ 예외를 잡지 못한다. 그래서 `optimize`가 던지면 JS 쪽에서
  복구할 수 없이 모듈이 멈춘다. 그래서 `optimize`가 던질 조건(검증 실패, k < 1)을 경계 함수가 **미리** 모두 검사하고 오류 코드로
  돌려준다. 34줄에서 k ≥ 1, 76줄에서 `validate`를 통과했으므로 78줄의 `optimize`는 `invalid_argument`를 던질 조건에 걸리지 않는다.
  `try/catch`가 없는 것은 실수가 아니라 이 설계 때문이다.
- **오류 문자열(12줄, 100줄).** 파일 안의 전역 `std::string` 하나. `trip_last_error()`는 그 `c_str()`를 돌려준다. 다음 호출이 33줄에서
  지우므로 포인터는 다음 호출 전까지만 의미가 있다.
- **출력 크기(26–28줄).** 계획 하나 = 요약 4 + 구간 수 1 + 구간 6 × (visits + 1) + 체류 수 1 + 체류 4 × visits. 여정은 항상 구간
  visits + 1개, 체류 visits개라서 이 크기는 상한이자 정확한 크기다. 예: visits = 8, k = 5면 5 × (4 + 1 + 54 + 1 + 32) = 460칸.
- **출력 쓰기(80–96줄).** `put` 람다가 `out[w++]`에 쓴다. `int64_t` 값은 `static_cast<double>`로 명시해서 바꾸고 `int`, `int32_t` 값은
  그대로 넘긴다. `-Wconversion`이 `int64_t → double`(정밀도 손실 가능)만 경고하기 때문이다. 계획이 k개보다 적으면 나머지 칸은 건드리지 않는다.
- 참고: 출력하는 `objective` 등이 2^53 이상이면 double로 바꿀 때 정밀도가 떨어질 수 있지만 코드는 이를 검사하지 않는다.

### 3.7 `trip_optimizer/engine/tests/test_optimizer.cpp` (252줄)

```cpp
#include <gtest/gtest.h>

#include <chrono>
#include <cstdio>
#include <random>
#include <set>
#include <stdexcept>

#include "brute_force.hpp"
#include "trip/optimizer.hpp"

namespace {

trip::Problem empty_problem(int visits, int days, int modes) {
    trip::Problem p;
    p.visits = visits;
    p.days = days;
    p.modes = modes;
    const size_t n = static_cast<size_t>(visits + 2);
    p.price.assign(n * n * static_cast<size_t>(days * modes), -1);
    p.minutes.assign(p.price.size(), 0);
    p.lodging.assign(n * static_cast<size_t>(days), 0);
    p.stay_min.assign(n, 1);
    p.stay_max.assign(n, 1);
    p.depart_min = 0;
    p.depart_max = 0;
    return p;
}

void set_leg(trip::Problem& p, int a, int b, int day, int mode, int64_t price, int32_t minutes = 60) {
    p.price[p.index(a, b, day, mode)] = price;
    p.minutes[p.index(a, b, day, mode)] = minutes;
}

trip::Problem random_problem(std::mt19937& rng) {
    std::uniform_int_distribution<int> visits(1, 4), days(2, 8), modes(1, 2), price(0, 500), minutes(10, 600),
        lodge(0, 100), stay(0, 2), extra(0, 2), cpm(0, 3), percent(0, 99);
    trip::Problem p = empty_problem(visits(rng), days(rng), modes(rng));
    for (size_t i = 0; i < p.price.size(); i++) {
        p.price[i] = percent(rng) < 25 ? -1 : price(rng);  // some options do not exist
        p.minutes[i] = minutes(rng);
    }
    for (size_t i = 0; i < p.lodging.size(); i++) p.lodging[i] = lodge(rng);
    for (int c = 1; c <= p.visits; c++) {
        p.stay_min[static_cast<size_t>(c)] = stay(rng);
        p.stay_max[static_cast<size_t>(c)] = p.stay_min[static_cast<size_t>(c)] + extra(rng);
    }
    p.depart_min = std::uniform_int_distribution<int>(0, p.days - 1)(rng);
    p.depart_max = std::uniform_int_distribution<int>(p.depart_min, p.days - 1)(rng);
    p.cost_per_minute = cpm(rng);
    return p;
}

// A plan must be a real itinerary, not just carry the right number.
void expect_valid_plan(const trip::Problem& p, const trip::Plan& plan) {
    ASSERT_EQ(plan.legs.size(), static_cast<size_t>(p.visits + 1));
    ASSERT_EQ(plan.stays.size(), static_cast<size_t>(p.visits));
    EXPECT_EQ(plan.legs.front().from, 0);
    EXPECT_EQ(plan.legs.back().to, p.visits + 1);
    EXPECT_GE(plan.legs.front().day, p.depart_min);
    EXPECT_LE(plan.legs.front().day, p.depart_max);
    std::set<int> seen;
    for (size_t i = 0; i < plan.stays.size(); i++) {
        const trip::Stay& s = plan.stays[i];
        EXPECT_TRUE(seen.insert(s.city).second) << "city visited twice";
        EXPECT_EQ(plan.legs[i].to, s.city);
        EXPECT_EQ(plan.legs[i + 1].from, s.city);
        EXPECT_EQ(plan.legs[i].day, s.arrive_day);
        EXPECT_EQ(plan.legs[i + 1].day, s.arrive_day + s.nights);
        EXPECT_GE(s.nights, p.stay_min[static_cast<size_t>(s.city)]);
        EXPECT_LE(s.nights, p.stay_max[static_cast<size_t>(s.city)]);
    }
    for (const trip::Leg& l : plan.legs) EXPECT_GE(l.price, 0) << "used a leg that does not exist";
    EXPECT_EQ(trip::evaluate(p, plan), plan.objective);
    EXPECT_EQ(plan.objective,
              plan.transport_price + plan.lodging_price + p.cost_per_minute * plan.travel_minutes);
}

}  // namespace

// The chat example: 4 cities -> 24 orders, flight prices change by date.
// Only one order is cheap, and only if the trip starts on day 1.
TEST(Optimizer, FindsTheOnlyCheapOrderAmong24) {
    trip::Problem p = empty_problem(4, 12, 1);
    for (int a = 0; a < p.nodes(); a++)
        for (int b = 0; b < p.nodes(); b++)
            for (int d = 0; d < p.days; d++) set_leg(p, a, b, d, 0, 300);
    p.depart_max = 3;
    // Cheap chain: origin -(day1)-> 3 -(day3)-> 1 -(day5)-> 4 -(day7)-> 2 -(day9)-> return
    const int chain[] = {0, 3, 1, 4, 2, 5};
    for (int i = 0; i < 5; i++) set_leg(p, chain[i], chain[i + 1], 1 + 2 * i, 0, 50);
    for (int c = 1; c <= 4; c++) p.stay_min[static_cast<size_t>(c)] = p.stay_max[static_cast<size_t>(c)] = 2;

    const auto plans = trip::optimize(p, 3);
    ASSERT_FALSE(plans.empty());
    EXPECT_EQ(plans[0].objective, 250);
    for (int i = 0; i < 5; i++) EXPECT_EQ(plans[0].legs[static_cast<size_t>(i)].to, chain[i + 1]);
    expect_valid_plan(p, plans[0]);
}

TEST(Optimizer, ValueForMoneyModeTradesPriceForTime) {
    trip::Problem p = empty_problem(1, 3, 2);  // mode 0 = cheap and slow, mode 1 = dear and fast
    for (int a : {0, 1})
        for (int d = 0; d < 3; d++) {
            set_leg(p, a, a + 1, d, 0, 100, 600);
            set_leg(p, a, a + 1, d, 1, 200, 60);
        }
    EXPECT_EQ(trip::optimize(p, 1)[0].legs[0].mode, 0);  // cheapest only
    p.cost_per_minute = 1;                               // one minute is worth 1 unit
    EXPECT_EQ(trip::optimize(p, 1)[0].legs[0].mode, 1);
}

TEST(Optimizer, InfeasibleTripReturnsNoPlans) {
    trip::Problem p = empty_problem(2, 5, 1);  // no legs exist at all
    EXPECT_TRUE(trip::optimize(p, 5).empty());
}

TEST(Optimizer, StayMustFitInsideTheWindow) {
    trip::Problem p = empty_problem(1, 3, 1);
    for (int d = 0; d < 3; d++) {
        set_leg(p, 0, 1, d, 0, 10);
        set_leg(p, 1, 2, d, 0, 10);
    }
    p.stay_min[1] = p.stay_max[1] = 3;  // 3 nights cannot fit in a 3-day window
    EXPECT_TRUE(trip::optimize(p, 1).empty());
}

TEST(Optimizer, RejectsMalformedInput) {
    trip::Problem p = empty_problem(2, 5, 1);
    p.depart_max = 9;
    EXPECT_THROW(trip::optimize(p, 1), std::invalid_argument);
    p = empty_problem(2, 5, 1);
    p.price.pop_back();
    EXPECT_THROW(trip::optimize(p, 1), std::invalid_argument);
    p = empty_problem(11, 2, 1);
    EXPECT_THROW(trip::optimize(p, 1), std::invalid_argument);
    EXPECT_THROW(trip::optimize(empty_problem(1, 2, 1), 0), std::invalid_argument);
}

// Property: on random small problems the k best objectives equal the k smallest
// values found by exhaustive enumeration, and every returned plan is a valid
// itinerary whose recomputed cost matches.
TEST(OptimizerProperty, MatchesBruteForceOnRandomProblems) {
    std::mt19937 rng(20261008);
    int feasible = 0;
    for (int trial = 0; trial < 3000; trial++) {
        const trip::Problem p = random_problem(rng);
        const int k = std::uniform_int_distribution<int>(1, 6)(rng);
        const auto plans = trip::optimize(p, k);
        const auto expected = oracle::all_costs(p);

        const size_t n = std::min(expected.size(), static_cast<size_t>(k));
        ASSERT_EQ(plans.size(), n) << "trial " << trial;
        for (size_t i = 0; i < n; i++) {
            ASSERT_EQ(plans[i].objective, expected[i]) << "trial " << trial << " rank " << i;
            expect_valid_plan(p, plans[i]);
        }
        if (!plans.empty()) feasible++;
    }
    // Guard against a generator that only makes infeasible problems (a vacuous pass).
    EXPECT_GT(feasible, 1000);
}

TEST(OptimizerProperty, SameInputSameOutput) {
    std::mt19937 rng(7);
    for (int trial = 0; trial < 200; trial++) {
        const trip::Problem p = random_problem(rng);
        const auto a = trip::optimize(p, 5), b = trip::optimize(p, 5);
        ASSERT_EQ(a.size(), b.size());
        for (size_t i = 0; i < a.size(); i++) {
            ASSERT_EQ(a[i].objective, b[i].objective);
            for (size_t j = 0; j < a[i].legs.size(); j++) {
                ASSERT_EQ(a[i].legs[j].to, b[i].legs[j].to);
                ASSERT_EQ(a[i].legs[j].day, b[i].legs[j].day);
                ASSERT_EQ(a[i].legs[j].mode, b[i].legs[j].mode);
            }
        }
    }
}

// Spec V4 target size: 8 cities, 30-day window, 3 modes, top 5. Prints the time;
// the budget is fixed after this first measurement, so only a loose bound here.
TEST(OptimizerPerformance, EightCitiesThirtyDays) {
    std::mt19937 rng(1);
    trip::Problem p = empty_problem(8, 30, 3);
    std::uniform_int_distribution<int> price(50, 900), minutes(30, 900);
    for (size_t i = 0; i < p.price.size(); i++) {
        p.price[i] = price(rng);
        p.minutes[i] = minutes(rng);
    }
    for (int c = 1; c <= 8; c++) {
        p.stay_min[static_cast<size_t>(c)] = 1;
        p.stay_max[static_cast<size_t>(c)] = 4;
    }
    p.depart_max = 7;
    const auto t0 = std::chrono::steady_clock::now();
    const auto plans = trip::optimize(p, 5);
    const double ms = std::chrono::duration<double, std::milli>(std::chrono::steady_clock::now() - t0).count();
    std::printf("[perf] 8 cities, 30 days, 3 modes, k=5: %.1f ms\n", ms);
    ASSERT_EQ(plans.size(), 5u);
    for (const auto& plan : plans) expect_valid_plan(p, plan);
    EXPECT_LT(ms, 10000.0);
}

// The C interface used by WebAssembly must return exactly what the C++ API returns.
#include "trip/c_api.h"

TEST(CApi, MatchesCppApiOnRandomProblems) {
    std::mt19937 rng(99);
    for (int trial = 0; trial < 300; trial++) {
        const trip::Problem p = random_problem(rng);
        const int k = 4;
        const std::vector<double> price(p.price.begin(), p.price.end());
        const std::vector<double> minutes(p.minutes.begin(), p.minutes.end());
        const std::vector<double> lodging(p.lodging.begin(), p.lodging.end());
        std::vector<double> out(static_cast<size_t>(trip_output_size(p.visits, k)));
        const int n = trip_optimize(p.visits, p.days, p.modes, price.data(), minutes.data(), lodging.data(),
                                    p.stay_min.data(), p.stay_max.data(), p.depart_min, p.depart_max,
                                    static_cast<double>(p.cost_per_minute), k, out.data(),
                                    static_cast<int>(out.size()));
        const auto plans = trip::optimize(p, k);
        ASSERT_EQ(n, static_cast<int>(plans.size())) << trip_last_error();
        size_t r = 0;
        for (const auto& plan : plans) {
            ASSERT_EQ(out[r], static_cast<double>(plan.objective));
            r += 4;
            const size_t legs = static_cast<size_t>(out[r++]);
            ASSERT_EQ(legs, plan.legs.size());
            for (const auto& l : plan.legs) {
                ASSERT_EQ(out[r], l.from);
                ASSERT_EQ(out[r + 1], l.to);
                ASSERT_EQ(out[r + 2], l.day);
                ASSERT_EQ(out[r + 3], l.mode);
                r += 6;
            }
            r += 1 + 4 * static_cast<size_t>(out[r]);
        }
    }
}

TEST(CApi, RejectsNonIntegerMoneyAndSmallBuffers) {
    trip::Problem p = empty_problem(1, 2, 1);
    std::vector<double> price(p.price.begin(), p.price.end()), minutes(p.minutes.begin(), p.minutes.end()),
        lodging(p.lodging.begin(), p.lodging.end());
    std::vector<double> out(static_cast<size_t>(trip_output_size(1, 1)));
    price[0] = 10.5;
    EXPECT_EQ(trip_optimize(1, 2, 1, price.data(), minutes.data(), lodging.data(), p.stay_min.data(),
                            p.stay_max.data(), 0, 0, 0, 1, out.data(), static_cast<int>(out.size())), -1);
    price[0] = -1;
    EXPECT_EQ(trip_optimize(1, 2, 1, price.data(), minutes.data(), lodging.data(), p.stay_min.data(),
                            p.stay_max.data(), 0, 0, 0, 1, out.data(), 1), -2);
}
```

해설 (도우미):

- `empty_problem`(14–28줄): 모든 구간 "없음"(가격 −1), 분 0, 숙박비 0, 모든 노드 박수 1..1, 출발일 0..0. 시험은 여기서 필요한 칸만 바꾼다.
- `set_leg`(30–33줄): 한 칸의 가격과 분(기본 60)을 쓴다.
- `random_problem`(35–52줄): V 1..4, D 2..8, M 1..2, 가격 0..500(25% 확률로 "없음"), 분 10..600, 숙박 0..100, 박수 최소 0..2 +
  폭 0..2, 출발 기간 무작위, cost_per_minute 0..3. **박수 0과 구간 없음이 섞이도록** 만들어 경계 사례를 자주 밟는다. V ≤ 4, D ≤ 8은 오라클이
  감당할 크기다(SPEC V1).
- `expect_valid_plan`(55–77줄, SPEC V2): 목적값만이 아니라 계획이 **실제 여정인지** 본다. 구간 수 V+1, 체류 수 V, 출발 노드 0에서 시작해 귀국
  노드로 끝남, 첫 출발일이 출발 기간 안, 도시 중복 없음, i번째 구간의 도착 도시 = i번째 체류 도시 = (i+1)번째 구간의 출발 도시,
  체류 도착일 = 들어온 구간의 날짜, 떠나는 날 = 도착일 + 박수, 박수 범위, 없는 구간(음수 가격) 사용 금지, `evaluate`로 다시 계산한 값 =
  목적값, 목적값 = 분해의 합.

해설 (시험 10개):

| 시험 | 무엇을 증명하나 |
|---|---|
| `FindsTheOnlyCheapOrderAmong24` (83–99줄) | 대화 속 예시: 도시 4개 → 순서 24가지. 모든 구간 300, 특정 사슬(0→3→1→4→2→귀국, 1·3·5·7·9일)만 50, 박수 2 고정, 출발 0..3일. 1일 출발 + 그 순서만 250이 된다. 순서·출발일·박수가 함께 맞아야 하는 문제를 푸는지 |
| `ValueForMoneyModeTradesPriceForTime` (101–111줄) | 수단 0 = 100원 600분, 수단 1 = 200원 60분. cpm 0이면 2 × 100 = 200 대 400 → 수단 0, cpm 1이면 2 × 700 = 1400 대 2 × 260 = 520 → 수단 1. 가성비 가중치가 실제로 선택을 바꾸는지 |
| `InfeasibleTripReturnsNoPlans` (113–116줄) | 구간이 하나도 없으면 예외가 아니라 빈 결과 |
| `StayMustFitInsideTheWindow` (118–126줄) | 기간 3일에 3박은 불가능(떠나는 날 ≥ 3). 기간 경계 처리 |
| `RejectsMalformedInput` (128–138줄) | 출발 기간 밖, 배열 크기 불일치, 도시 11개, k = 0이 모두 `invalid_argument` |
| `MatchesBruteForceOnRandomProblems` (143–162줄) | SPEC V1+V2. 시드 20261008로 무작위 문제 3000개, k 1..6. 결과 수 = min(오라클 수, k), 각 순위의 목적값 = 오라클 값, 각 계획이 실제 여정. 마지막 `feasible > 1000`은 생성기가 불가능한 문제만 만들어 "아무것도 비교하지 않고 통과"하는 일을 막는 장치 |
| `SameInputSameOutput` (164–179줄) | 같은 입력을 두 번 풀면 목적값과 구간의 도착 도시·날짜·수단이 같다. 같은 실행 파일 안의 결정성만 본다(위 3.4절 (3)의 실험 참고) |
| `EightCitiesThirtyDays` (183–203줄) | SPEC의 성능 목표 크기(V = 8, D = 30, M = 3, K = 5). 시간을 출력하고, 상한은 10초로 느슨하게. 결과 5개가 모두 실제 여정인지도 확인. 주석은 "Spec V4"라고 쓰지만 현재 SPEC v0.2 표에서 성능 예산은 V5, V4는 네이티브 = WASM이다 |
| `MatchesCppApiOnRandomProblems` (208–239줄) | C 인터페이스 결과가 C++ API와 같은지. 입력 정수를 double 배열로 바꿔 넘기고, 출력 배열을 배치대로 걸어가며(요약 4칸 건너뛰고, 구간 수, 구간당 6칸, 그리고 236줄에서 체류 수 1칸 + 체류당 4칸 건너뛰기) 목적값과 구간 from/to/day/mode를 비교 |
| `RejectsNonIntegerMoneyAndSmallBuffers` (241–252줄) | 가격 10.5 → −1. 가격 −1(정수라 통과)에 버퍼 길이 1 → −2. 검사 순서상 변환이 먼저, 버퍼 검사가 나중이라는 것도 같이 확인된다 |

**심은 결함(seeded bug) 시험 — 시험 자체의 검출력(SPEC V3).** 커밋 메시지에 따르면 원 작성자는 박수 범위 off-by-one, 기간 경계
off-by-one, 상위 K 정리 오류 세 가지를 심어 모두 잡히는 것을 확인했다. 다만 그 결함 버전은 저장소에 코드로 남아 있지 않다.
그래서 이 문서를 쓰며 원본을 `/tmp/claude-0/` 아래에 복사해 한 줄씩 바꾸고 `ctest`를 다시 돌렸다. 결과(클라우드 세션 측정):

| 심은 결함 (optimizer.cpp) | 실패한 시험 | 읽을거리 |
|---|---|---|
| 115줄 `s <= stay_max` → `s < stay_max` (박수 상한 빠짐) | #1 Failed, #2 SegFault, #6 Failed | #2는 박수가 1..1이라 계획이 0개가 되어 `optimize(p, 1)[0]`이 빈 벡터를 읽는다. 시험이 `ASSERT_FALSE(plans.empty())` 없이 `[0]`을 쓰기 때문이다 |
| 115줄 `s = stay_min` → `s = stay_min + 1` (박수 하한 밀림) | #1 Failed, #2 SegFault, #6 Failed | 위와 같은 양상 |
| 117줄 `d >= days` → `d >= days - 1` (기간 마지막 날 제외) | #6만 Failed | 손 사례들은 마지막 날을 쓰지 않아서 못 잡는다. 무작위 성질 시험이 잡는다 |
| 117줄 `d >= days` → `d > days` (기간 밖 하루 허용) | #6 Failed, #7 SegFault, #9 SegFault | `d == days`면 `sidx`와 `Problem::index`가 다른 상태·다른 구간의 칸을, 경우에 따라 배열 밖을 가리켜 정의되지 않은 동작이 된다 |
| 52줄 `keep_best`에서 정렬 제거 (상위 K 정리 오류) | #1, #2, #6 Failed | 남는 k개가 가장 싼 k개가 아니고 최종 목록도 정렬되지 않아 1등 목적값부터 틀린다 |
| 61줄 `nth_element` 기준을 `begin()`으로 (자를 때 앞 k개가 아님) | #6만 Failed | 후보가 4k를 넘고 k ≥ 2일 때만 드러나는 결함 (k = 1이면 `begin() + k − 1 == begin()`이라 원래와 같다) |
| 137줄 `r < here.size()` → `r < 1` (이전 상태의 1등만 이어 붙임) | #6만 Failed | 1등만 잇는 DP는 k = 1에서는 맞다. k ≥ 2가 섞인 무작위 시험만 잡는다 |
| 170줄 `stays` 뒤집기 제거 (역추적 오류) | #1, #6, #8 Failed | #6의 첫 실패는 66줄 `legs[i].to == s.city`. 목적값은 맞고 계획만 틀린 결함이라 V2 검사(`expect_valid_plan`)가 있어야 잡힌다 |
| 33–38줄 `better`를 비용만 비교 | 없음 (10/10 통과) | 3.4절 (3) 참고. 현재 시험으로는 못 잡는 결함 |

이 표가 보여 주는 것: 손으로 만든 사례 5개만으로는 기간 경계, `nth_element`, K-best 병합 결함을 하나도 못 잡는다. 결함 대부분을
잡는 것은 오라클과 비교하는 #6이고, 역추적 결함은 #6 안의 `expect_valid_plan`이 잡는다. 반대로 동점 순서 결함은 지금 시험으로는 드러나지 않는다.

## 4. 연습 문제

1. **K-best 병합 다시 짜기.** `keep_best`와 `push_bounded`를 지우고, 상태마다 크기 k의 최대 힙(`std::priority_queue`, 비교는 `better`)을
   유지하는 방식으로 다시 짠다. `prev_rank`가 가리키는 순위가 정렬 순서여야 한다는 점(100줄)을 지켜야 한다.
   `ctest --test-dir build -R 'OptimizerProperty'`로 V1과 결정성 시험이 통과하는지, 성능 시험 시간이 어떻게 바뀌는지 본다.
2. **박수 범위 off-by-one 심기.** 115줄의 `<=`를 `<`로 바꾸고 `ctest --test-dir build --output-on-failure`. 어느 시험이 어떤 메시지로
   실패하는지 위 표와 비교한다. 그다음 `ValueForMoneyModeTradesPriceForTime`이 SegFault 대신 깔끔하게 실패하도록 시험을 고쳐 본다
   (힌트: `[0]` 앞에 `ASSERT_FALSE(...empty())`).
3. **기간 경계 off-by-one 심기.** 117줄을 `d >= p_.days - 1`로 바꾸면 #6만 실패한다. 이 결함을 잡는 **손 사례 시험**을 하나 새로 써 본다
   (예: 기간 3일, 도시 1개, 출발 1일 고정, 1박, 0→1 구간은 1일에만, 1→귀국 구간은 마지막 날인 2일에만 있음. 이 문서를 쓰며 확인한 값:
   원본 엔진은 계획 1개, 이 결함을 심은 엔진은 0개).
4. **동점 순서 결함을 잡는 시험 설계.** `better`를 비용만 비교하게 바꾸면 10/10이 통과한다(3.4절 (3)). 비용이 같은 여정이 여럿인 문제를
   만들고, 반환된 계획의 순서가 `(prev_state, prev_rank, nights, day, mode)` 규칙대로인지 직접 기대값을 적어 검사하는 시험을 써 본다.
5. **숙박비 누적합을 반복문으로.** `lodging()`(194–196줄)을 날짜 반복 합으로 바꿔도 시험이 통과하는지 확인하고,
   `./build/trip_tests --gtest_filter='OptimizerPerformance.*'`의 `[perf]` 시간을 바꾸기 전후로 세 번씩 재 본다. 숫자는 자기 기계에서 잰 것만 적는다.
6. **역추적만 망가뜨리기.** 170줄(`stays` 뒤집기)을 지우면 목적값은 그대로인데 어떤 검사가 실패하는지 확인한다. `expect_valid_plan`의
   각 줄 중 무엇이 이 결함을 잡는지 하나씩 주석 처리해 가며 찾아본다.
7. **C 경계값 시험.** `price[0] = 9007199254740991.0`(2^53 − 1)은 받아들이고 `9007199254740992.0`(2^53)은 −1을 돌려주는지,
   `NaN`과 `minutes = 2147483648.0`(INT32_MAX + 1)도 −1인지 확인하는 시험을 `CApi` 묶음에 추가한다.
8. **상태 표 크기 손계산.** V = 10, D = 30일 때 `states_` 칸 수와, 성능 시험 문제(V = 8, D = 30, M = 3, 박수 1..4, K = 5)에서 넣기 횟수
   상한(3.4절 (8)의 식)을 손으로 계산한다. 그다음 `run()`에 카운터를 임시로 넣어 실제 `push_bounded` 호출 수와 비교한다.

## 5. 빌드·시험 명령

저장소 루트(`analy_agent/`)에서:

```bash
cmake -S trip_optimizer/engine -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build
ctest --test-dir build --output-on-failure
```

자주 쓰는 변형:

```bash
ctest --test-dir build -R CApi                                   # 이름에 CApi가 든 시험만
./build/trip_tests --gtest_filter='OptimizerPerformance.*'       # [perf] 줄을 보려면 실행 파일을 직접
./build/trip_tests --gtest_filter='OptimizerProperty.*'          # V1·결정성 시험만
```

- 첫 configure는 FetchContent로 GoogleTest `v1.15.2`를 받으므로 네트워크가 필요하다.
- `-B`로 소스 밖에 빌드 폴더를 두면 소스 트리는 바뀌지 않는다.

이 문서를 쓰며 실제로 돌린 결과 (클라우드 세션 측정: Intel Xeon Processor @ 2.80GHz, vCPU 4개, Ubuntu GCC 13.3.0, CMake 3.28.3, Release,
빌드 폴더 `/tmp/claude-0/engine_doc/build`, 소스는 커밋 `5a1d016` 그대로):

```text
 1/10 Test  #1: Optimizer.FindsTheOnlyCheapOrderAmong24 ...............   Passed    0.00 sec
 2/10 Test  #2: Optimizer.ValueForMoneyModeTradesPriceForTime .........   Passed    0.00 sec
 3/10 Test  #3: Optimizer.InfeasibleTripReturnsNoPlans ................   Passed    0.00 sec
 4/10 Test  #4: Optimizer.StayMustFitInsideTheWindow ..................   Passed    0.00 sec
 5/10 Test  #5: Optimizer.RejectsMalformedInput .......................   Passed    0.00 sec
 6/10 Test  #6: OptimizerProperty.MatchesBruteForceOnRandomProblems ...   Passed    0.06 sec
 7/10 Test  #7: OptimizerProperty.SameInputSameOutput .................   Passed    0.01 sec
 8/10 Test  #8: OptimizerPerformance.EightCitiesThirtyDays ............   Passed    0.09 sec
 9/10 Test  #9: CApi.MatchesCppApiOnRandomProblems ....................   Passed    0.01 sec
10/10 Test #10: CApi.RejectsNonIntegerMoneyAndSmallBuffers ............   Passed    0.00 sec
100% tests passed, 0 tests failed out of 10
Total Test time (real) =   0.18 sec
```

위는 두 번째 실행이다. 첫 실행(빌드 직후)도 요약 줄은 `100% tests passed, 0 tests failed out of 10`으로 같았고 `Total Test time (real) =   0.21 sec`였다.
성능 시험의 `[perf]` 줄을 세 번 따로 실행해 얻은 값(클라우드 세션 측정):

```text
[perf] 8 cities, 30 days, 3 modes, k=5: 90.8 ms
[perf] 8 cities, 30 days, 3 modes, k=5: 88.3 ms
[perf] 8 cities, 30 days, 3 modes, k=5: 85.2 ms
```

시험 실행 파일 전체를 한 번 직접 돌렸을 때 GoogleTest 요약은 `10 tests from 4 test suites ran. (159 ms total)`, `[  PASSED  ] 10 tests.`였다.
3장 끝의 심은 결함 표도 같은 기계에서, 원본을 복사한 폴더(`/tmp/claude-0/engine_doc/mut/<이름>/`)마다 한 줄만 바꿔 같은 명령으로 얻은 결과다.
