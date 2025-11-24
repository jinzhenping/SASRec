# 새로운 데이터셋 추가 가이드

## 빠른 시작

### 1단계: 데이터 파일 준비

`python/data/` 폴더에 다음 형식의 텍스트 파일을 저장하세요:

```
user_id item_id
1 100
1 200
1 150
2 100
2 300
...
```

**중요 사항:**
- 사용자 ID와 아이템 ID는 **1부터 시작**해야 합니다
- 각 라인은 하나의 상호작용을 나타냅니다
- **시간 순서대로 정렬**되어 있어야 합니다 (마지막 2개가 valid/test로 사용됨)
- 공백으로 구분된 두 개의 정수입니다

### 2단계: 학습 실행

```bash
python main.py --dataset=your_dataset_name --train_dir=default --device=cuda --maxlen=200
```

예시:
```bash
# 데이터 파일이 python/data/my_dataset.txt 인 경우
python main.py --dataset=my_dataset --train_dir=default --device=cuda --maxlen=200
```

## 데이터 전처리 (다른 형식인 경우)

원본 데이터가 다른 형식(CSV, TSV 등)인 경우 `prepare_new_dataset.py` 스크립트를 사용하세요:

### CSV 파일 변환 예시

```bash
python prepare_new_dataset.py \
    --input your_data.csv \
    --output data/my_dataset.txt \
    --user_col user_id \
    --item_col item_id \
    --time_col timestamp \
    --delimiter ,
```

### TSV 파일 변환 예시

```bash
python prepare_new_dataset.py \
    --input your_data.tsv \
    --output data/my_dataset.txt \
    --user_col user_id \
    --item_col item_id \
    --time_col timestamp \
    --delimiter "\t"
```

## 데이터 형식 요구사항

### 필수 형식
- 파일명: `python/data/{dataset_name}.txt`
- 각 라인: `{user_id} {item_id}` (공백으로 구분)
- ID 범위: 1부터 시작하는 연속된 정수
- 정렬: 사용자별로 시간 순서대로 정렬

### 데이터 분할 방식
코드는 자동으로 train/valid/test로 분할합니다:
- **4개 미만의 상호작용**: 모두 train에 포함 (valid/test 없음)
- **4개 이상의 상호작용**: 
  - 마지막 2개: valid(1개) + test(1개)
  - 나머지: train

## 하이퍼파라미터 튜닝 가이드

데이터셋 특성에 따라 하이퍼파라미터를 조정하세요:

### 작은 데이터셋 (< 10K 사용자)
```bash
python main.py \
    --dataset=your_dataset \
    --maxlen=50 \
    --dropout_rate=0.5 \
    --hidden_units=50 \
    --num_blocks=2 \
    --num_heads=1 \
    --lr=0.001 \
    --batch_size=128
```

### 큰 데이터셋 (> 100K 사용자)
```bash
python main.py \
    --dataset=your_dataset \
    --maxlen=200 \
    --dropout_rate=0.2 \
    --hidden_units=50 \
    --num_blocks=2 \
    --num_heads=1 \
    --lr=0.001 \
    --batch_size=128
```

### Pre-LN 사용 (더 나은 성능)
```bash
python main.py \
    --dataset=your_dataset \
    --maxlen=200 \
    --norm_first \
    --dropout_rate=0.2
```

## 예시: 전체 워크플로우

```bash
# 1. 데이터 전처리 (필요한 경우)
python prepare_new_dataset.py \
    --input raw_data.csv \
    --output data/my_dataset.txt

# 2. 데이터 확인
head python/data/my_dataset.txt

# 3. 학습 실행
python main.py \
    --dataset=my_dataset \
    --train_dir=default \
    --device=cuda \
    --maxlen=200 \
    --norm_first

# 4. 결과 확인
# 결과는 my_dataset_default/log.txt에 저장됩니다
cat my_dataset_default/log.txt
```

## 문제 해결

### 오류: "FileNotFoundError: data/your_dataset.txt"
- 파일이 `python/data/` 폴더에 있는지 확인
- 파일명이 정확한지 확인 (확장자 `.txt` 포함)

### 오류: "ValueError: invalid literal for int()"
- 데이터 형식이 올바른지 확인 (공백으로 구분된 두 정수)
- 빈 라인이 없는지 확인

### 성능이 낮은 경우
- `maxlen`을 평균 시퀀스 길이에 맞게 조정
- `dropout_rate` 조정 (0.2 ~ 0.5)
- `norm_first` 옵션 사용
- 학습 epoch 수 확인

