import json
import os
import time

EPSILON = 1e-9


def normalize_label(raw_label: str) -> str:
    """
    입력된 필터 키나 expected 라벨을 표준 라벨('Cross', 'X')로 정규화합니다.
    """
    if not isinstance(raw_label, str):
        return str(raw_label)

    cleaned = raw_label.strip().lower()
    if cleaned in ("+", "cross"):
        return "Cross"
    elif cleaned in ("x",):
        return "X"
    return raw_label.strip()


def validate_square_matrix(matrix, expected_size=None) -> tuple[bool, str, int]:
    """
    2차원 리스트가 정방행렬(N x N)인지, 모든 요소가 숫자인지 검증합니다.
    반환값: (유효성 여부, 오류 메시지, 행렬 크기 N)
    """
    if not isinstance(matrix, list) or len(matrix) == 0:
        return False, "데이터가 비어있거나 2차원 배열 형식이 아닙니다.", 0

    n = len(matrix)
    if expected_size is not None and n != expected_size:
        return False, f"행 크기 불일치 (기대: {expected_size}, 실제: {n})", n

    for r_idx, row in enumerate(matrix):
        if not isinstance(row, list) or len(row) != n:
            actual_cols = len(row) if isinstance(row, list) else -1
            return False, f"{r_idx + 1}번째 행의 열 크기 불일치 (기대: {n}, 실제: {actual_cols})", n
        for c_idx, val in enumerate(row):
            if not isinstance(val, (int, float)) or isinstance(val, bool):
                return False, f"({r_idx + 1}, {c_idx + 1}) 위치에 숫자가 아닌 값이 포함됨: {val}", n

    return True, "", n


def mac_operation(pattern: list[list[float]], filter_matrix: list[list[float]]) -> float:
    """
    외부 라이브러리 없이 이중 반복문을 사용하여 MAC(Multiply-Accumulate) 연산을 수행합니다.
    """
    n = len(pattern)
    total_score = 0.0
    for i in range(n):
        for j in range(n):
            total_score += pattern[i][j] * filter_matrix[i][j]
    return total_score


def compare_scores(score_a: float, score_b: float, label_a: str, label_b: str, epsilon: float = EPSILON) -> str:
    """
    허용오차(epsilon) 정책을 적용하여 두 필터 점수를 비교하고 판정 결과를 반환합니다.
    """
    if abs(score_a - score_b) < epsilon:
        return "UNDECIDED"
    elif score_a > score_b:
        return label_a
    else:
        return label_b


def measure_mac_performance(pattern: list[list[float]], filter_matrix: list[list[float]], iterations: int = 10) -> float:
    """
    I/O를 제외한 순수 MAC 연산 함수 호출 시간을 iterations회 반복 측정하여 평균 시간(ms)을 반환합니다.
    """
    # 워밍업 1회
    mac_operation(pattern, filter_matrix)

    start_time = time.perf_counter()
    for _ in range(iterations):
        mac_operation(pattern, filter_matrix)
    end_time = time.perf_counter()

    avg_ms = ((end_time - start_time) / iterations) * 1000.0
    return avg_ms


def input_matrix_3x3(name: str) -> list[list[float]]:
    """
    사용자로부터 3x3 행렬을 한 줄씩(공백 구분) 입력받고 유효성을 검증합니다.
    """
    print(f"{name} (3줄 입력, 공백 구분)")
    matrix = []
    row_idx = 0
    while row_idx < 3:
        raw_input = input().strip()
        parts = raw_input.split()
        if len(parts) != 3:
            print("입력 형식 오류: 각 줄에 3개의 숫자를 공백으로 구분해 입력하세요.")
            continue
        try:
            row = [float(x) for x in parts]
            matrix.append(row)
            row_idx += 1
        except ValueError:
            print("입력 형식 오류: 숫자만 입력할 수 있습니다. 다시 입력하세요.")
    return matrix


def generate_patterns(n: int) -> tuple[list[list[float]], list[list[float]]]:
    """
    [보너스 과제] 크기 N을 입력받아 N x N 크기의 십자가(Cross)와 X 패턴을 자동 생성합니다.
    """
    cross = [[0.0] * n for _ in range(n)]
    x_pat = [[0.0] * n for _ in range(n)]
    mid = n // 2

    for i in range(n):
        for j in range(n):
            # 십자가 패턴: 중앙 행 또는 중앙 열
            if i == mid or j == mid:
                cross[i][j] = 1.0
            # X 패턴: 주대각선 또는 부대각선
            if i == j or (i + j) == (n - 1):
                x_pat[i][j] = 1.0

    return cross, x_pat


def run_mode_1():
    """
    모드 1: 사용자 입력 (3x3) 처리 흐름
    """
    print("\n#---------------------------------------")
    print("# [1] 필터 입력")
    print("#---------------------------------------")
    filter_a = input_matrix_3x3("필터 A")
    print()
    filter_b = input_matrix_3x3("필터 B")

    print("\n#---------------------------------------")
    print("# [2] 패턴 입력")
    print("#---------------------------------------")
    pattern = input_matrix_3x3("패턴")

    # MAC 연산 및 성능 측정 (10회 반복 평균)
    score_a = mac_operation(pattern, filter_a)
    score_b = mac_operation(pattern, filter_b)
    avg_time_ms = measure_mac_performance(pattern, filter_a, iterations=10)

    decision = compare_scores(score_a, score_b, "A", "B")

    print("\n#---------------------------------------")
    print("# [3] MAC 결과")
    print("#---------------------------------------")
    # 부동소수점 미세 오차 확인이 용이하도록 출력 포맷 조정
    if decision == "UNDECIDED":
        print(f"A 점수: {score_a:.16f}")
        print(f"B 점수: {score_b:.16f}")
        print(f"연산 시간(평균/10회): {avg_time_ms:.3f} ms")
        print(f"판정: 판정 불가 (|A-B| < {EPSILON})")
    else:
        print(f"A 점수: {score_a}")
        print(f"B 점수: {score_b}")
        print(f"연산 시간(평균/10회): {avg_time_ms:.3f} ms")
        print(f"판정: {decision}")

    print("\n#---------------------------------------")
    print("# [4] 성능 분석 (3x3)")
    print("#---------------------------------------")
    print(f"{'크기':<10} {'평균 시간(ms)':<15} {'연산 횟수'}")
    print("-" * 37)
    print(f"{'3 x 3':<10} {avg_time_ms:<15.4f} {3 * 3}")


def run_mode_2(filepath: str = "data.json"):
    """
    모드 2: data.json 로드, 스키마 검증, 라벨 정규화, 일괄 판정 및 성능 분석 흐름
    """
    if not os.path.exists(filepath):
        print(f"\n[오류] '{filepath}' 파일을 찾을 수 없습니다. 같은 디렉토리에 파일이 있는지 확인하세요.")
        return

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"\n[오류] JSON 파싱 실패: {e}")
        return

    raw_filters = data.get("filters", {})
    raw_patterns = data.get("patterns", {})

    print("\n#---------------------------------------")
    print("# [1] 필터 로드")
    print("#---------------------------------------")
    normalized_filters = {}  # { size_int: {"Cross": matrix, "X": matrix} }

    for size_key, filter_dict in raw_filters.items():
        # size_5 -> 5 추출
        try:
            size_n = int(size_key.split("_")[1])
        except (IndexError, ValueError):
            print(f"✗ {size_key}: 잘못된 필터 크기 키 형식입니다.")
            continue

        if not isinstance(filter_dict, dict):
            print(f"✗ {size_key}: 필터 데이터가 딕셔너리 형식이 아닙니다.")
            continue

        normalized_filters[size_n] = {}
        loaded_labels = []

        for raw_f_key, matrix in filter_dict.items():
            std_label = normalize_label(raw_f_key)
            is_valid, err_msg, _ = validate_square_matrix(matrix, expected_size=size_n)
            if is_valid and std_label in ("Cross", "X"):
                normalized_filters[size_n][std_label] = matrix
                loaded_labels.append(std_label)
            else:
                print(f"✗ {size_key} ({raw_f_key}) 로드 경고: {err_msg}")

        if "Cross" in normalized_filters[size_n] and "X" in normalized_filters[size_n]:
            print(f"✓ {size_key:<7} 필터 로드 완료 ({', '.join(loaded_labels)})")
        else:
            print(f"✗ {size_key:<7} 필수 필터(Cross, X) 누락")

    print("\n#---------------------------------------")
    print("# [2] 패턴 분석 (라벨 정규화 적용)")
    print("#---------------------------------------")
    total_tests = 0
    passed_tests = 0
    failed_cases = []

    for pat_key, pat_info in raw_patterns.items():
        total_tests += 1
        print(f"--- {pat_key} ---")

        if not isinstance(pat_info, dict):
            reason = "스키마 오류: 패턴 항목이 객체 형식이 아님"
            print(f"판정: ERROR | FAIL ({reason})")
            failed_cases.append((pat_key, reason))
            continue

        # 키에서 크기 N 추출 (예: size_5_1 -> 5)
        try:
            parts = pat_key.split("_")
            if len(parts) < 3 or parts[0] != "size":
                raise ValueError
            target_n = int(parts[1])
        except ValueError:
            reason = "키 규칙 오류: 'size_{N}_{idx}' 형식이 아님"
            print(f"판정: ERROR | FAIL ({reason})")
            failed_cases.append((pat_key, reason))
            continue

        input_matrix = pat_info.get("input")
        raw_expected = pat_info.get("expected", "")
        expected_label = normalize_label(raw_expected)

        # 해당 크기의 필터 존재 여부 확인
        if target_n not in normalized_filters or "Cross" not in normalized_filters[target_n] or "X" not in normalized_filters[target_n]:
            reason = f"필터 누락: size_{target_n}에 대한 유효한 필터가 없음"
            print(f"판정: ERROR | expected: {expected_label} | FAIL ({reason})")
            failed_cases.append((pat_key, reason))
            continue

        # 입력 패턴 크기 및 타입 검증
        is_valid, err_msg, _ = validate_square_matrix(input_matrix, expected_size=target_n)
        if not is_valid:
            reason = f"크기/데이터 불일치: {err_msg}"
            print(f"판정: ERROR | expected: {expected_label} | FAIL ({reason})")
            failed_cases.append((pat_key, reason))
            continue

        # MAC 연산 수행
        cross_filter = normalized_filters[target_n]["Cross"]
        x_filter = normalized_filters[target_n]["X"]

        cross_score = mac_operation(input_matrix, cross_filter)
        x_score = mac_operation(input_matrix, x_filter)
        decision = compare_scores(cross_score, x_score, "Cross", "X")

        # 점수 출력 (미세 오차 확인을 위해 동점일 경우 소수점 16자리 출력)
        if decision == "UNDECIDED":
            print(f"Cross 점수: {cross_score:.16f}")
            print(f"X 점수: {x_score:.16f}")
        else:
            print(f"Cross 점수: {cross_score}")
            print(f"X 점수: {x_score}")

        if decision == expected_label:
            passed_tests += 1
            print(f"판정: {decision} | expected: {expected_label} | PASS")
        else:
            if decision == "UNDECIDED":
                reason = f"동점(UNDECIDED) 처리 규칙에 따라 FAIL (|Cross-X| < {EPSILON})"
            else:
                reason = f"판정 불일치 (예측: {decision}, 정답: {expected_label})"
            print(f"판정: {decision} | expected: {expected_label} | FAIL ({reason})")
            failed_cases.append((pat_key, reason))

    print("\n#---------------------------------------")
    print("# [3] 성능 분석 (평균/10회)")
    print("#---------------------------------------")
    print(f"{'크기':<10} {'평균 시간(ms)':<15} {'연산 횟수'}")
    print("-" * 37)

    # 3x3 포함하여 5x5, 13x13, 25x25 등 표준 크기 측정
    benchmark_sizes = [3, 5, 13, 25]
    for size_n in benchmark_sizes:
        # data.json에 해당 크기 필터가 있으면 활용, 없으면 패턴 생성기로 생성하여 측정
        if size_n in normalized_filters and "Cross" in normalized_filters[size_n]:
            f_mat = normalized_filters[size_n]["Cross"]
            p_mat, _ = generate_patterns(size_n)
        else:
            p_mat, _ = generate_patterns(size_n)
            f_mat, _ = generate_patterns(size_n)

        avg_ms = measure_mac_performance(p_mat, f_mat, iterations=10)
        size_str = f"{size_n} x {size_n}"
        print(f"{size_str:<10} {avg_ms:<15.4f} {size_n * size_n}")

    print("\n#---------------------------------------")
    print("# [4] 결과 요약")
    print("#---------------------------------------")
    print(f"총 테스트: {total_tests}개")
    print(f"통과: {passed_tests}개")
    print(f"실패: {len(failed_cases)}개")

    if failed_cases:
        print("\n실패 케이스:")
        for case_id, reason in failed_cases:
            print(f"- {case_id}: {reason}")


def run_bonus_pattern_generator():
    """
    [보너스 과제] 패턴 생성기 실행 및 즉시 MAC 테스트
    """
    print("\n#---------------------------------------")
    print("# [보너스] N x N 패턴 자동 생성기")
    print("#---------------------------------------")
    while True:
        raw_n = input("생성할 패턴의 크기 N을 입력하세요 (홀수 권장, 예: 5): ").strip()
        try:
            n = int(raw_n)
            if n < 3:
                print("3 이상의 정수를 입력하세요.")
                continue
            break
        except ValueError:
            print("올바른 정수를 입력하세요.")

    cross_pat, x_pat = generate_patterns(n)

    print(f"\n[생성된 {n} x {n} Cross 패턴]")
    for row in cross_pat:
        print(" ".join(str(int(v)) for v in row))

    print(f"\n[생성된 {n} x {n} X 패턴]")
    for row in x_pat:
        print(" ".join(str(int(v)) for v in row))

    avg_ms = measure_mac_performance(cross_pat, x_pat, iterations=10)
    score_cross_to_cross = mac_operation(cross_pat, cross_pat)
    score_cross_to_x = mac_operation(cross_pat, x_pat)

    print(f"\n[자가 검증 MAC 테스트 (입력: Cross)]")
    print(f"Cross 필터 점수: {score_cross_to_cross} | X 필터 점수: {score_cross_to_x}")
    print(f"판정: {compare_scores(score_cross_to_cross, score_cross_to_x, 'Cross', 'X')}")
    print(f"평균 연산 시간(10회): {avg_ms:.4f} ms (연산 횟수: {n * n}회)")


def main():
    while True:
        print("\n=== Mini NPU Simulator ===")
        print("\n[모드 선택]")
        print("1. 사용자 입력 (3x3)")
        print("2. data.json 분석")
        print("3. [보너스] N x N 패턴 생성기")
        print("0. 종료")

        choice = input("선택: ").strip()

        if choice == "1":
            run_mode_1()
        elif choice == "2":
            run_mode_2("data.json")
        elif choice == "3":
            run_bonus_pattern_generator()
        elif choice == "0":
            print("시뮬레이터를 종료합니다.")
            break
        else:
            print("잘못된 선택입니다. 0~3 사이의 번호를 입력하세요.")


if __name__ == "__main__":
    main()