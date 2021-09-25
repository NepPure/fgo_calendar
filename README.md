# fgo_calendar

FGO图形化活动日历插件，Fork的公主连接版本，适用于 `HoshinoBot v2`.

项目地址 <https://github.com/NepPure/fgo_calendar>

原神的👇

<https://github.com/NepPure/genshin_calendar>

![calendar](preview.png)

## 日程信息源

官网新闻，正则匹配的，没有识别出日期的就直接过滤了

## 安装方法

1. 在HoshinoBot的插件目录modules下clone本项目 `git clone https://github.com/NepPure/fgo_calendar.git`
1. 在 `config/__bot__.py`的模块列表里加入 `fgo_calendar`
1. 重启HoshinoBot

## 指令列表

- `fgo日历` : 查看本群订阅服务器日历
- `fgo日历 on/off` : 订阅/取消订阅指定服务器的日历推送
- `fgo日历 time 时:分` : 设置日历推送时间
- `fgo日历 status` : 查看本群日历推送设置
- `fgo日历 cardimage` : (go-cqhttp限定)切换是否使用cardimage模式发送日历图片
