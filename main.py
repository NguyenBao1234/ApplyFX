import sys
from Core.audio_engine import AudioEngine

TEST_FILE = "test-sound.wav"
def main():
    engine = AudioEngine()

    try:
        filepath = TEST_FILE
        engine.load(filepath)
        print(" Load thành công!")
        print(f"   {engine.info_str}")
        print(f"   Số mẫu  : {len(engine.samples):,}")
        print(f"   Dtype   : {engine.samples.dtype}")
        print(f"   Min/Max : {engine.samples.min():.4f} / {engine.samples.max():.4f}")
    except (ValueError, RuntimeError) as e:
        print(f"[x] Lỗi: {e}")


if __name__ == "__main__":
    main()