import math

def get_embedding(text):
    if "苹果" in text or "Apple" in text:
        return [0.1, 0.9]
    elif "香蕉" in text or "Banana" in text:
        return [0.2, 0.8]
    elif "橙子" in text or "Orange" in text:
        return [0.3, 0.7]
    elif "卡车" in text or "Truck" in text:
        return [0.9, 0.1]
    else:
        return [0.5, 0.5]
    
def euclidean_distance(v1, v2):
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(v1, v2)))

vec_apple = get_embedding("苹果")
vec_banana = get_embedding("香蕉")
vec_truck = get_embedding("卡车")

dist_apple_banana = euclidean_distance(vec_apple, vec_banana)
dist_apple_truck = euclidean_distance(vec_apple, vec_truck)

print(f"苹果 <-> 香蕉 距离：{dist_apple_banana: .4f}")
print(f"苹果 <-> 卡车 距离: {dist_apple_truck: .4f}")