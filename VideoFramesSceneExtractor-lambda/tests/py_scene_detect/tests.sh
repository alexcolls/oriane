# 1) Content detector, very sensitive cuts, single‐frame scenes
python advanced.py \
  --detector content \
  --threshold 25.0 \
  --min-scene-len 30 \
  --workers 1 \
  --output-dir content

# 2) Threshold detector, medium sensitivity, longer scenes
python advanced.py \
  --detector threshold \
  --threshold 5.0 \
  --min-scene-len 30 \
  --workers 1 \
  --output-dir threshold

# 3) Histogram detector, catching fades/dissolves
python advanced.py \
  --detector histogram \
  --threshold 0.3 \
  --min-scene-len 30 \
  --workers 1 \
  --output-dir histogram
