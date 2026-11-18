#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Mini NPU Simulator: 반복문 기반 MAC 연산으로 패턴 유사도를 계산한다."""

import json
import math
import re
import time
from pathlib import Path

EPSILON = 1e-9
REPEAT_COUNT = 10
STANDARD_LABELS = ("Cross", "X")


def normalize_label(value):
    """입력 라벨을 내부 표준 라벨(Cross/X)로 변환한다."""
    if not isinstance(value, str):
        return None
    key = value.strip().lower()
    if key in ("cross", "+"):
        return "Cross"
    if key in ("x",):
        return "X"
    return None


def parse_matrix(matrix, expected_size=None):
    """정사각형 2차원 배열인지 확인하고 float 행렬로 변환한다."""
    if not isinstance(matrix, list) or not matrix:
        raise ValueError("행렬은 비어 있지 않은 2차원 배열이어야 합니다.")

    size = len(matrix)
    if expected_size is not None and size != expected_size:
        raise ValueError(
            "행렬 크기 불일치: 기대 크기 {}x{}, 실제 행 수 {}".format(
                expected_size, expected_size, size
            )
        )

    result = []
    for row_index, row in enumerate(matrix, start=1):
        if not isinstance(row, list) or len(row) != size:
            actual = len(row) if isinstance(row, list) else "배열 아님"
            raise ValueError(
                "{}행의 열 개수가 올바르지 않습니다. 기대 {}, 실제 {}".format(
                    row_index, size, actual
                )
            )
        converted = []
        for value in row:
            if isinstance(value, bool):
                raise ValueError("행렬에는 숫자만 입력할 수 있습니다.")
            try:
                number = float(value)
            except (TypeError, ValueError):
                raise ValueError("숫자로 변환할 수 없는 값이 있습니다: {!r}".format(value))
            if not math.isfinite(number):
                raise ValueError("NaN 또는 무한대 값은 사용할 수 없습니다.")
            converted.append(number)
        result.append(converted)
    return result


def mac(pattern, filter_matrix):
    """같은 위치의 값을 곱해 모두 더하는 MAC 연산(O(N^2))."""
    n = len(pattern)
    if n != len(filter_matrix):
        raise ValueError("패턴과 필터의 행 크기가 다릅니다.")

    total = 0.0
    for row in range(n):
        if len(pattern[row]) != n or len(filter_matrix[row]) != n:
            raise ValueError("패턴과 필터는 같은 크기의 정사각형이어야 합니다.")
        for col in range(n):
            total += pattern[row][col] * filter_matrix[row][col]
    return total


def decide(score_a, score_b):
    """두 점수 차이가 epsilon 미만이면 동점으로 판정한다."""
    if abs(score_a - score_b) < EPSILON:
        return "UNDECIDED"
    return "A" if score_a > score_b else "B"


def decide_labels(cross_score, x_score):
    """JSON 분석용 표준 라벨 판정."""
    if abs(cross_score - x_score) < EPSILON:
        return "UNDECIDED"
    return "Cross" if cross_score > x_score else "X"


def measure_average(pattern, filter_matrix, repeat_count=REPEAT_COUNT):
    """I/O를 제외하고 MAC 함수 호출만 repeat_count회 측정한다."""
    start = time.perf_counter()
    for _ in range(repeat_count):
        mac(pattern, filter_matrix)
    elapsed_ms = (time.perf_counter() - start) * 1000.0
    return elapsed_ms / repeat_count


def generate_pattern(size, label):
    """성능 측정용 정사각형 Cross/X 패턴을 생성한다."""
    if size < 1:
        raise ValueError("크기는 1 이상이어야 합니다.")
    result = []
    for row in range(size):
        line = []
        for col in range(size):
            if label == "Cross":
                value = 1 if row == size // 2 or col == size // 2 else 0
            else:
                value = 1 if row == col or row + col == size - 1 else 0
            line.append(float(value))
        result.append(line)
    return result


def read_matrix_from_console(name, size=3):
    """행 단위로 입력받고 형식 오류가 있으면 해당 행을 다시 입력받는다."""
    print("{} ({}줄 입력, 각 줄에 숫자 {}개)".format(name, size, size))
    matrix = []
    for row_index in range(size):
        while True:
            raw = input("{}행: ".format(row_index + 1)).strip()
            parts = raw.split()
            if len(parts) != size:
                print("입력 형식 오류: 각 줄에 {}개의 숫자를 공백으로 구분해 입력하세요.".format(size))
                continue
            try:
                values = [float(part) for part in parts]
                if not all(math.isfinite(value) for value in values):
                    raise ValueError
            except ValueError:
                print("입력 형식 오류: 유효한 숫자만 입력하세요.")
                continue
            matrix.append(values)
            break
    return matrix


def run_manual_mode():
    print("\n" + "=" * 56)
    print("[1] 필터 입력")
    filter_a = read_matrix_from_console("필터 A")
    filter_b = read_matrix_from_console("필터 B")

    print("\n입력된 필터를 저장했습니다.")
    print("A 필터:", filter_a)
    print("B 필터:", filter_b)

    print("\n[2] 패턴 입력")
    pattern = read_matrix_from_console("패턴")

    print("\n[3] MAC 결과")
    score_a = mac(pattern, filter_a)
    score_b = mac(pattern, filter_b)
    elapsed_a = measure_average(pattern, filter_a)
    elapsed_b = measure_average(pattern, filter_b)
    result = decide(score_a, score_b)

    print("A 점수: {:.12g}".format(score_a))
    print("B 점수: {:.12g}".format(score_b))
    print("연산 시간(평균/{}회): A {:.6f} ms, B {:.6f} ms".format(
        REPEAT_COUNT, elapsed_a, elapsed_b
    ))
    if result == "UNDECIDED":
        print("판정: 판정 불가 (|A-B| < {})".format(EPSILON))
    else:
        print("판정: {}".format(result))

    print("\n[4] 성능 분석")
    print_performance_table([3])


def extract_size(pattern_key):
    match = re.match(r"^size_(\d+)_", str(pattern_key))
    if not match:
        raise ValueError("케이스 키에서 크기 N을 추출할 수 없습니다: {}".format(pattern_key))
    return int(match.group(1))


def load_json_data(path):
    with open(path, "r", encoding="utf-8") as file:
        data = json.load(file)
    if not isinstance(data, dict):
        raise ValueError("JSON 최상위 구조는 객체여야 합니다.")
    if not isinstance(data.get("filters"), dict):
        raise ValueError("'filters' 항목이 없거나 객체 형식이 아닙니다.")
    if not isinstance(data.get("patterns"), dict):
        raise ValueError("'patterns' 항목이 없거나 객체 형식이 아닙니다.")
    return data


def get_filter_pair(filters, size):
    size_key = "size_{}".format(size)
    if size_key not in filters:
        raise ValueError("{} 필터가 없습니다.".format(size_key))

    size_filters = filters[size_key]
    if not isinstance(size_filters, dict):
        raise ValueError("{} 필터는 객체 형식이어야 합니다.".format(size_key))

    normalized = {}
    for raw_label, matrix in size_filters.items():
        label = normalize_label(raw_label)
        if label is None:
            continue
        if label in normalized:
            raise ValueError("{}에 중복된 {} 필터 라벨이 있습니다.".format(size_key, label))
        normalized[label] = parse_matrix(matrix, size)

    missing = [label for label in STANDARD_LABELS if label not in normalized]
    if missing:
        raise ValueError("{}에 필수 필터가 없습니다: {}".format(size_key, ", ".join(missing)))
    return normalized["Cross"], normalized["X"]


def analyze_json_patterns(data):
    patterns = data["patterns"]
    total = 0
    passed = 0
    failures = []
    sizes_for_benchmark = {3, 5, 13, 25}

    print("\n" + "=" * 56)
    print("[1] 필터 로드")
    filter_cache = {}
    for size in (5, 13, 25):
        try:
            filter_cache[size] = get_filter_pair(data["filters"], size)
            print("✓ size_{} 필터 로드 완료 (Cross, X)".format(size))
        except (ValueError, TypeError) as error:
            print("✗ size_{} 필터 로드 실패: {}".format(size, error))

    print("\n[2] 패턴 분석 (라벨 정규화 적용)")
    for case_id, case in patterns.items():
        total += 1
        try:
            if not isinstance(case, dict):
                raise ValueError("케이스 데이터는 객체 형식이어야 합니다.")

            size = extract_size(case_id)
            sizes_for_benchmark.add(size)
            if size not in filter_cache:
                filter_cache[size] = get_filter_pair(data["filters"], size)

            pattern = parse_matrix(case.get("input"), size)
            expected = normalize_label(case.get("expected"))
            if expected is None:
                raise ValueError(
                    "expected 라벨을 Cross/X로 정규화할 수 없습니다: {!r}".format(
                        case.get("expected")
                    )
                )

            cross_filter, x_filter = filter_cache[size]
            cross_score = mac(pattern, cross_filter)
            x_score = mac(pattern, x_filter)
            result = decide_labels(cross_score, x_score)
            is_pass = result == expected
            if is_pass:
                passed += 1
                status = "PASS"
            else:
                status = "FAIL"
                reason = (
                    "판정 불일치 (판정={}, expected={})".format(result, expected)
                    if result != "UNDECIDED"
                    else "동점 규칙에 따라 UNDECIDED (expected={})".format(expected)
                )
                failures.append((case_id, reason))

            print("\n--- {} ---".format(case_id))
            print("Cross 점수: {:.12g}".format(cross_score))
            print("X 점수: {:.12g}".format(x_score))
            print("판정: {} | expected: {} | {}".format(result, expected, status))

        except (ValueError, TypeError, KeyError) as error:
            reason = str(error)
            failures.append((case_id, reason))
            print("\n--- {} ---".format(case_id))
            print("FAIL: {}".format(reason))

    print("\n[3] 성능 분석 (평균/{}회)".format(REPEAT_COUNT))
    print_performance_table(sorted(sizes_for_benchmark))

    failed = total - passed
    print("\n[4] 결과 요약")
    print("총 테스트: {}개".format(total))
    print("통과: {}개".format(passed))
    print("실패: {}개".format(failed))
    if failures:
        print("\n실패 케이스:")
        for case_id, reason in failures:
            print("- {}: {}".format(case_id, reason))
    else:
        print("\n실패 케이스가 없습니다.")


def print_performance_table(sizes):
    print("{:<12} {:>18} {:>16}".format("크기", "평균 시간(ms)", "연산 횟수(N²)"))
    print("-" * 50)
    for size in sizes:
        pattern = generate_pattern(size, "Cross")
        filter_matrix = generate_pattern(size, "Cross")
        average_ms = measure_average(pattern, filter_matrix)
        print("{:<12} {:>18.6f} {:>16}".format(
            "{}x{}".format(size, size), average_ms, size * size
        ))


def main():
    print("=== Mini NPU Simulator ===")
    while True:
        print("\n[모드 선택]")
        print("1. 사용자 입력 (3x3)")
        print("2. data.json 분석")
        choice = input("선택: ").strip()

        if choice == "1":
            try:
                run_manual_mode()
            except (KeyboardInterrupt, EOFError):
                print("\n입력이 취소되었습니다.")
            return
        if choice == "2":
            path_text = input("data.json 경로 (기본값: ./data.json): ").strip()
            path = Path(path_text) if path_text else Path("data.json")
            try:
                data = load_json_data(path)
                analyze_json_patterns(data)
            except FileNotFoundError:
                print("파일을 찾을 수 없습니다: {}".format(path))
            except json.JSONDecodeError as error:
                print("JSON 형식 오류: {}".format(error))
            except (OSError, ValueError) as error:
                print("데이터 로드 오류: {}".format(error))
            return

        print("잘못된 선택입니다. 1 또는 2를 입력하세요.")


if __name__ == "__main__":
    main()
