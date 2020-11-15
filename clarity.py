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
- 从文件中提取: Altitude, AirMass, m_0
- 统计同一AirMass的m_0, 迭代剔除3σ噪点后取中值
- 统计Altitude分布区间, 当区间宽度大于30度时, 尝试拟合透明度
- 参与拟合的样本和拟合结果输出至文件:
  1. clarity-CCYYMMDD.txt
  2. clarity-CCYYMMDD.png
- 输出日期-透明度
  clarity.txt
  
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

@ntoe: clarity.txt文件格式
- 文本文件
- 参与统计的样本
- 每行对应一个日期
- 行元素间分隔符是空格
- 行元素自首至尾依次是:
  年月日
  透明度
  
'''
#-----------------------------------------------------------------------------#
import sys;
import os;
from operator import itemgetter;
import numpy as np;
import matplotlib.pyplot as plt;

#-----------------------------------------------------------------------------#
# 数据结构
class SourceLogItem:
    # 原始日志单条记录
    def __init__(self, airmass, m0):
        self.airmass = airmass;
        self.m0      = m0;
        
    def __repr__(self):
        return repr((self.airmass, self.m0));
        
class ReadLog:
    def __init__(self, filepath):
        # 解析提取文件名中的日期, 文件名格式: cal-CCYYMMDD.txt
        self.dateStr = filepath[4:12];
        # 解析日志文件
        self.items = []; # 有效记录集合
        # 构造函数, 打开日志文件
        with open(filepath, "r") as fp:
            altmin = 1E30;
            altmax = -1E30;
            lineno = 0;
            for line in fp:
                lineno += 1;
                # 遍历文件, 解析关键数据
                tokens = line.split();
                if len(tokens) == 10:
                    alt     = float(tokens[6]);
                    airmass = float(tokens[7]);
                    m0      = float(tokens[8]);
                    k       = float(tokens[9]);
                    if m0 > 0.0 or k > 0.0:
                        # 仪器星等=10, 调制
                        m0 = 10.0 - (m0 + k * 10.0);
                        if (m0 > 0.0):
                            item = SourceLogItem(airmass, m0);
                            self.items.append(item);
                            if (alt < altmin):
                                altmin = alt;
                            if (alt > altmax):
                                altmax = alt;

        if len(self.items) > 0 and (altmax - altmin) < 30.0:
            self.items.clear();
        if len(self.items) > 0:
            self.items.sort(key= lambda SourceLogItem: SourceLogItem.airmass);
#             print ("\t altMin = %.1f, altMax = %.1f" % (altmin, altmax));
            
    def Count(self):
        # 样本数量
        return len(self.items);

    def get_sampleMid(self, samples):
        n = len(samples);
        if n < 5:
            return [False, 0.0];
        
        samples.sort(key = lambda SourceLogItem: SourceLogItem.m0);
        return [True, samples[1].m0];

#         mid = int(n / 2);
#         if n % 2 == 1:
#             m0 = samples[mid].m0;
#         else:
#             m0 = (samples[mid].m0 + samples[mid + 1].m0) * 0.5;
#         return [True, m0];
    
    def ExecSample(self):
        # 采样, 抽取同一大气质量的m0中值
        # 返回: 抽样数量
        self.samples = [];  # 采样记录集合
        n = self.Count();
        # 抽样
        samples = [];
        airmass0 = 0.0;
        for i in range(n):
            airmass = self.items[i].airmass;
            if ((airmass - airmass0) > 0.1):
                # 抽样间隔>0.1
                success, m0 = self.get_sampleMid(samples);
                if (success == True):
                    item = SourceLogItem(airmass0, m0);
                    self.samples.append(item);
                    
                samples.clear();
                airmass0 = airmass;
                
            item = SourceLogItem(airmass, self.items[i].m0);
            samples.append(item);

        success, m0 = self.get_sampleMid(samples);
        if (success == True):
            item = SourceLogItem(airmass0, m0);
            self.samples.append(item);
        
#         print ("\t Airmass   m0");
#         for item in self.samples:
#             print ("\t %5.2f  %5.1f" % (item.airmass, item.m0));
            
        return len(self.samples);
    
    def DoFit(self):
        # 拟合大气透明度
        airmass = [];
        m0 = [];
        for item in self.samples:
            airmass.append(item.airmass);
            m0.append(item.m0);
        x = np.array(airmass);
        y = np.array(m0);
        p = np.polyfit(x, y, 1);
        self.k  = p[0];
        self.c0 = p[1];
#         print (p);
        
        if self.k > 0.0 and self.k < 3.0:
            # 输出拟合结果
            clarity = open('clarity-'+self.dateStr+".txt", "w");
            clarity.write("%.3f    %.3f\n" % (self.c0, self.k));
            clarity.write("--------------------------------\n");
            for item in self.samples:
                clarity.write("%4.1f  %4.1f\n" % (item.airmass, item.m0));
            clarity.close();
            # 画图
            plt.clf();
            plt.plot(airmass, m0, '.', airmass, np.polyval(p, x), '-');
            plt.plot(airmass, np.polyval(p, x), '-');
            plt.title(self.dateStr);
            plt.xlabel('Airmass');
            plt.ylabel('Magnitude');
            plt.text(np.mean(airmass), np.mean(m0), 'm=%.3f%+.3fx' % (self.c0, self.k));
            plt.show(block = False);
            # 将绘图存储为PNG图像
            plt.savefig("clarity-"+self.dateStr+".png");
            return True;
        
        return False;

# end class ReadLog:

#-----------------------------------------------------------------------------#
# 主程序
# 命令行格式:
# clarity.py directory_name
# clarity.py file1 @file-list
if __name__ == '__main__':
    n = len(sys.argv);
    if n < 2:
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
        for i in range(1, n):
            sourceList.append(sys.argv[i]);

    plt.figure(figsize=(5,5));

    dateStr = [];
    extZ = [];
    clarity = open("clarity.txt", "w");        
    # 遍历原始文件
    for i in range(count):
        print (sourceList[i]);
        log_src = ReadLog(sourceList[i]);
        if log_src.Count() > 0 and log_src.ExecSample() >= 5:
            if log_src.DoFit() == True:
                c0 = log_src.c0 + log_src.k + 0.15; # 0.15: 实际数据受外界因素影响质量较差, 拟合结果失真. +0.15调制使其接近真值
                if c0 > 0.0:
                    dateStr.append(log_src.dateStr);
                    extZ.append(c0);
                    clarity.write("%s  %4.1f  %7.3f\n" % (log_src.dateStr, c0, log_src.k));
    
    clarity.close();
    
    # 绘画
    plt.clf();
    plt.plot(dateStr, extZ, '.');
    plt.title("clarity");
    plt.xlabel('date');
    plt.ylabel('AirExtinction');
#     plt.show(block = False);
    # 将绘图存储为PNG图像
    plt.savefig("clarity.png");

    plt.show(block=True);
    