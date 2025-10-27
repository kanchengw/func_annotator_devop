def rotate_array(arr, k):
    length = len(arr)
    k = k % length
    return arr[-k:] + arr[:-k]

def triangle_area(a, b, c):
    s = (a + b + c) / 2
    return (s * (s - a) * (s - b) * (s - c)) **0.5

def reverse_integer(x):
    sign = -1 if x < 0 else 1
    reversed_num = int(str(abs(x))[::-1])
    return sign * reversed_num if reversed_num.bit_length() < 32 else 0