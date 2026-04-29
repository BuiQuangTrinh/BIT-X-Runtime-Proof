import pandas as pd
import matplotlib.pyplot as plt

# Đọc dữ liệu
df = pd.read_csv("results.csv")

# Tạo biểu đồ
plt.figure(figsize=(6,4))

plt.plot(df["coverage"], df["energy_sim"], marker='o')

plt.xlabel("Coverage (fraction of data processed)")
plt.ylabel("Energy (simulated)")
plt.title("BIT-X4 Trade-off Curve")

plt.grid(True)
plt.tight_layout()

# Lưu ảnh
plt.savefig("x4_curve.png")

# Hiển thị
plt.show()
