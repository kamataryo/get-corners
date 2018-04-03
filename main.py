#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import numpy
import cv2
import itertools
import sys

map = sys.argv[1] #引数は作業ディレクトリ内の画像ファイルの名前。

gray = cv2.imread(map, 0) #画像の読み込み。第2引数を0にするとグレースケールとして読み込む。

ret, converted = cv2.threshold(gray, 175, 255, cv2.THRESH_BINARY_INV) # 二値画像へ変換。1つ目に戻り値 (retへ代入) は無視してよい。
height, width  = gray.shape
noframe = cv2.rectangle(converted, (0, 0), (width, height), (0, 0, 0), 1500) #画像の左上、右下の点を基準とする太さ1500pxの長方形を描画。マージンを塗りつぶすため。

kernel = numpy.ones((14, 14), numpy.uint8) #erodeのkernelを設定。
eroded = cv2.erode(noframe, kernel, iterations = 1) #図中の境界を削る。細い線を除去して太い枠だけを残すため。

lines = cv2.HoughLines(eroded, 4, numpy.pi/90, 5000) #辺の候補となる直線 (θとρで表す) を取得。引数は対象画像、ρの精度、θの精度、線分の閾値。この時点で直線の数は4本より多い。

# 直線を4本に絞るため、近接する直線の組み合わせをすべて取得。直線は番号で表される。
deletion_indexes = []
for indexed_line1 in enumerate(lines):
    for indexed_line2 in enumerate(lines):
        if indexed_line1[0] != indexed_line2[0]:
            line1 = indexed_line1[1][0]
            line2 = indexed_line2[1][0]
            rho1 = line1[0]
            theta1 = line1[1]
            rho2 = line2[0]
            theta2 = line2[1]
            if abs(rho1 - rho2) < 100 and abs(theta1 - theta2) < numpy.pi/18:
                deletion_indexes.append([indexed_line1[0], indexed_line2[0]])

# 近接する直線を近接グループに分ける。
merged_indexes = [deletion_indexes[1]]
for deletion_set in deletion_indexes:
    counter = 0
    for i, merged_set in enumerate(merged_indexes):
        if set(deletion_set).intersection(merged_set):
            merged_indexes[i] = merged_indexes[i] + deletion_set
            break
        counter = counter + 1
        if counter == len(merged_indexes):
            merged_indexes.append(deletion_set)

index_groups = [list(set(i)) for i in merged_indexes] # 各グループにおける直線の番号の重複を除去。

sides1 = [i[0] for i in index_groups] # 各グループから直線を1本ずつ取得。残りは捨てる。

# 近接するすべての直線を取得。
grouped_indexes = []
for sublist in index_groups:
    for element in sublist:
        grouped_indexes.append(element)

sides2 = list(set(list(range(len(lines)))).difference(grouped_indexes)) # すべての直線と近接する直線の差をとる。つまり近接する直線のない独立した直線を取得。

sides = [lines[i] for i in sides1 + sides2] #辺となる4直線の番号のリスト。

# 4直線の傾きとy軸との交点を取得。
slopes = []
intersections = []
for side in sides:
    side = side[0]
    slope = -(1/numpy.tan(side[1]))
    slopes.append(slope)
    intersection = side[0] * 1/numpy.sin(side[1])
    intersections.append(intersection)

xysides = list(zip(slopes, intersections)) # y = ax + bで表される直線のaとbのリスト。
xyrtsides = list(zip(xysides, sides)) #4辺のa, b, rho, thetaのリスト。

# 4辺の交点4つの座標を取得。
corners = []
for two_sides in itertools.combinations(xyrtsides, 2):
    side1 = two_sides[0]
    side2 = two_sides[1]
    xyside1 = side1[0]
    xyside2 = side2[0]
    rtside1 = side1[1][0]
    rtside2 = side2[1][0]
    if xyside1[0] == xyside2[0]:
        pass
    else:
        if not numpy.isfinite(xyside1[0]):
            x = rtside1[0]
            y = xyside2[0]*x + xyside2[1]
        elif not numpy.isfinite(xyside2[0]):
            x = rtside2[0]
            y = xyside1[0]*x + xyside1[1]
        else:
            x = - (xyside2[1] - xyside1[1]) / (xyside2[0] - xyside1[0])
            y = xyside1[0] + xyside1[1]
        x = int(x)
        y = int(y)
        corners.append([x, y])

upper_left = min(corners, key=sum) #左上の頂点の座標。
lower_right = max(corners, key=sum) #右下の頂点の座標。

upper_left = [element + 210 for element in upper_left] #外側の太い枠から内側の細い枠まで頂点の座標を210ピクセルずらす。
lower_right = [element - 210 for element in lower_right]

color = cv2.imread(map, 1) #地図をカラーで読み込む。
color = cv2.rectangle(color, tuple(upper_left), tuple(lower_right), (0, 0, 255), 25) # 長方形を描画。

#頂点の座標を出力。
# for corner in corners:
#     print(corner)
print(corners)


# cv2.imwrite('frame_map.jpg', color) #長方形を描画した地図を出力。
