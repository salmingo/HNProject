#!/usr/bin/env python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------#
'''
@file clarity.py
@brief 计算大气透明度
@note: 
依赖库:
- matplot

@note: 
- 遍历文件夹下cal-CCYYMMDD.txt格式的文件, 或者
- 遍历命令行输入的文件
- 从文件中提取: FWHM, Altitude, AirMass, m_0
- 统计同一AirMass的m_0, 迭代剔除3σ噪点后取中值
- 统计Altitude分布区间, 当区间宽度大于30度时, 尝试拟合透明度
- 参与拟合的样本和拟合结果输出至文件:
  1. clarity-CCYYMMDD.txt
  2. clarity-CCYYMMDD.png
- 当时间跨度大于10天时, 输出日期-透明度
  3. clarity.txt
  4. clarity.png
  
@note: cal-CCYYMMDD.txt文件格式
- 文本文件
- 每行对应一帧图像的定标结果
- 行元素间分隔符是空格
- 行元素自首至尾依次是:
文件名
曝光中间时标, 格式: CCYY-MM-DDThh:mm:ss.ssssss
半高全宽
赤经-ICRS
赤纬-ICRS
方位
高度
大气质量
修正零点
修正斜率

@note: clarity-CCYYMMDD.txt文件格式
- 文本文件
- 两个单元.
  单元1: 透明度拟合结果(零点, 斜率=透明度, 残差)
  单元2: 样本
- 单元间使用==========作为分隔标志
- 单元2格式:
  1. 行对应数据点, 分隔符是空格
  2. 行元素自首至尾依次是:
  大气质量
  图像定标的修正零点
  高度

@ntoe: clarity.txt文件格式
- 文本文件
- 参与统计的样本
- 每行对应一个日期
- 行元素间分隔符是空格
- 行元素自首至尾依次是:
  年
  月
  日
  透明度
  
'''
#-----------------------------------------------------------------------------#
import sys
import os
import matplotlib.pyplot as plt

#-----------------------------------------------------------------------------#
# 数据结构
    
#-----------------------------------------------------------------------------#
# 计算

#-----------------------------------------------------------------------------#
# 绘画

#-----------------------------------------------------------------------------#
# 输出

#-----------------------------------------------------------------------------#
# 主程序
# 命令行格式:
# clarity.py directory_name
# clarity.py file1 @file-list
if __name__ == '__main__':
    n = len(sys.argv);
    if len(sys.argv) < 2:
        print ("Usage: clarity.py directory_name");
        print ("Usage: clarity.py file1 @file-list");
        sys.exit(1);

    # 原始文件
    sourceList = [];
    count = 0;
    if os.path.isdir(sys.argv[1]):
        dirname = sys.argv[1];
        # 扫描文件夹
        print ("scan directory ", dirname);
        for filename in os.listdir(dirname):
            filepath = os.path.join(dirname, filename);
            if os.path.isfile(filepath):
                name, ext = os.path.split(filename);
                if name.find("cal-") == 0 and ext == ".txt":
                    count += 1;
                    sourceList.append(filepath);
                    
        sourceList.sort();
    else:
        count = n - 1;
        for i in range(n):
            sourceList.append(sys.argv[i]);
        

    # 打开画图窗口
    plt.figure(figsize=(5,5));
    plt.show(block = False);

    # 遍历原始文件
    for i in range(count):
        print (sourceList[i]);
        
    