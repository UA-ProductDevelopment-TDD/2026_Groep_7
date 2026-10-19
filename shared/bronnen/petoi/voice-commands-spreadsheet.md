# voice-commands-spreadsheet

| | |
|---|---|
| Link in de slides | https://docs.google.com/spreadsheets/d/1Lr6Cd1T-H9sSdUi_bI-OeMClkVOKjTQM/ |
| Opgehaald van | https://docs.google.com/spreadsheets/d/1Lr6Cd1T-H9sSdUi_bI-OeMClkVOKjTQM/export?format=xlsx |
| Opgehaald op | 2026-10-06 |
| HTTP-status | 200 |
| Methode | xlsx-export van de spreadsheet, beide tabbladen omgezet naar CSV; celopmaak niet overgenomen |

---

## Tabblad: English

```csv
List of voice commands supported by the voice command module which is included with Bittle X,,,,,,
Index,Voice command,"Return value to Serial2
（9600 Baud,ASCII）",Audio response,Explanation,,"Customized command code
for Petoi mobile app"
Customized  by user,To be defined 1,XA\11\n,Di,"DiDi
↓
Please speak the first command 
↓
Learning success / Learning failure, please say it again
↓
Please speak the second command 
↓
......
↓
DiDiDi",,
,To be defined 2,XA\12\n,Di,,,
,To be defined 3,XA\13\n,Di,,,
,To be defined 4,XA\14\n,Di,,,
,To be defined 5,XA\15\n,Di,,,
,To be defined 6,XA\16\n,Di,,,
,To be defined 7,XA\17\n,Di,,,
,To be defined 8,XA\18\n,Di,,,
,To be defined 9,XA\19\n,Di,,,
,To be defined\10,XA\20\n,Di,,,
1,Stand up,XA\21kup\n,Ok,"When the audio response is turned on, 
it will automatically play the audio response
after receiving the voice command, 
and the voice module will send the serial command to the MCU",,kup
2,sit,XA\22ksit\n,Ok,,,ksit
3,stretch,XA\23kstr\n,Nice,,,kstr
4,push ups,XA\24kpu\n,ok,,,kpu
5,Cheers,XA\25kchr\n,Cheers,,,kchr
6,Hello,XA\26khi\n,hello,,,khi
7,Come here,XA\27kcmh\n,What's up?,,,kcmh
8,check,XA\28kck\n,what's wrong？,,,kck
9,step,XA\29kvtF\n,Ok,,,kvtF
10,spin,XA\30kvtLX\n,Ok,,,kvtLX
11,crawl,XA\31kcrF\n,Ok,,,kcrF
12,walk,XA\32kwkF\n,Ok,,,kwkF
13,retreat,XA\33kbk\n,Ok,,,kbk
14,push,XA\34kphF\n,Ok,,,kphF
15,kick,XA\35kkc\n,Get away!,,,kkc
16,play dead,XA\36kpd\n,Ouch,,,kpd
17,pee,XA\37kpee\n,Mark,,,kpee
18,hug,XA\38khg\n,hug me,,,khg
19,hands up,XA\39khu\n,Agreed,,,khu
20,handstand,XA\40khds\n,Watch out,,,khds
21,roll back up,XA\41krc\n,No problem,,,krc
22,scratch,XA\42kscrh\n,Nice,,,kscrh
23,dig,XA\43kdg\n,good stuff,,,kdg
24,sniff,XA\44ksnf\n,What's this?,,,ksnf
25,go to sleep,XA\45kwh\n,Oh，no,,,kwh
26,Do you want some food?,XA\46knd\n,Of course!,,,knd
27,high five,XA\47kfiv\n,Give me five,,,kfiv
28,backflip,XA\48kbf\n,Watch out,,,kbf
29,frontflip,XA\49kff\n,Let me try,,,kff
30,handshake,XA\50khsk\n,Nice to meet you,,,khsk
31,Good boy,XA\51kgdb\n,So happy!,,,kgdb
32,Be table,XA\52ktbl\n,freeze,,,ktbl
33,boxing,XA\53kbx\n,fighting ,,,kbx
34,jump,XA\54kjmp\n,I can fly,,,kjmp
35,climb up,XA\55kclup\n,Let me try,,,kclup
36,leap over,XA\56klpov\n,Let me try,,,klpov
37,angry,XA\57kang\n,I'm angry!,,,kang
38,Pet toy,XA\58kx\n,Di,,,kx
39,attention,XA\59c\n,Yes sir!,,,c
40,rest,XA\60d\n,ok,,,d
"Configuration 
Commands",Bing-Bing,XAA,Switch to English,,,
,Di-Di,XAB,Switch to Chinese,,,
,Play sound,XAC,Tone 1-3-5,Turn on the audio response and enable reaction,,
,Be quiet,XAD,Tone 5-3-1,Turn off the audio response and stop reaction,,
,start learning,XAE,Di-Di,start learning,,
,stop learning,XAF,Di-Di-Di,stop learning,,
,clear the learning data,XAG,All cleared,clear the learning data,,
,,,,,,
List of Serial Commands,,,,,,
Serial commands,"Customized command code
for Petoi mobile app*","Return value to Serial2
（9600 Baud,ASCII）",Audio response,Explanation,Note,
XAa,"X65,97",=A63,Switch to English,,MCU sends a serial command to the voice module (sending command are the same as receiving command),
XAb,"X65,98",=A64,Switch to Chinese,,,
XAc,"X65,99",=A65,Tone 1-3-5,Turn on the audio response and enable reaction,,
XAd,"X65,100",=A66,Tone 5-3-1,Turn off the audio response and disable reaction,,
XAe,"X65,101",=A67,Di-Di,start learning,,
XAf,"X65,102",=A68,Di-Di-Di,stop learning,,
XAg,"X65,103",=A69,All cleared,clear the learning data,,
,,,,,,
* You can add a custom command button on the Petoi Mobile App to enable manually switching to English mode in case your robot is not responsive to your voice commands,,,,,,
Petoi Mobile App command,,,,,,
Customized command code,,,Explanation,,,
"^X65,99;!1000;X65,98;!1000;X65,97",,,Reset the voice command module and switch to English,,,
```

## Tabblad: 中文

```csv
List of Voice Commands,,,,,,
序号,语音指令,"串口返回值
（9600波特率,ASCII码)",提示音播报,说明,,可在移动端应用配置的命令来触发各种动作
自定义指令,(待定义指令1),XA\11\n,嘀,"嘀嘀
↓
请说出第一条命令
↓
学习成功/学习失败请再说一次
↓
请说出第二条命令
↓
......
↓
嘀嘀嘀",,
,(待定义指令2),XA\12\n,嘀,,,
,(待定义指令3),XA\13\n,嘀,,,
,(待定义指令4),XA\14\n,嘀,,,
,(待定义指令5),XA\15\n,嘀,,,
,(待定义指令6),XA\16\n,嘀,,,
,(待定义指令7),XA\17\n,嘀,,,
,(待定义指令8),XA\18\n,嘀,,,
,(待定义指令9),XA\19\n,嘀,,,
,(待定义指令10),XA\20\n,嘀,,,
1,起立,XA\21kup\n,好的,当提示音打开时自动播报，语音模块发送给MCU,,kup
2,坐下,XA\22ksit\n,好的,,,ksit
3,伸懒腰,XA\23kstr\n,啊,,,kstr
4,俯卧撑,XA\24kpu\n,好的,,,kpu
5,加油,XA\25kchr\n,加油,,,kchr
6,你好,XA\26khi\n,你好,,,khi
7,过来,XA\27kcmh\n,什么事？,,,kcmh
8,观察,XA\28kck\n,有情况,,,kck
9,踏步,XA\29kvtF\n,好的,,,kvtF
10,转圈圈,XA\30kvtLX\n,好的,,,kvtLX
11,向前爬,XA\31kcrF\n,好的,,,kcrF
12,前进,XA\32kwkF\n,好的,,,kwkF
13,后退,XA\33kbk\n,好的,,,kbk
14,推进,XA\34kphF\n,好的,,,kphF
15,踢腿,XA\35kkc\n,走开,,,kkc
16,装死,XA\36kpd\n,哎呦,,,kpd
17,撒尿,XA\37kpee\n,到此一游,,,kpee
18,抱抱,XA\38khg\n,抱抱,,,khg
19,举手,XA\39khu\n,同意,,,khu
20,倒立,XA\40khds\n,看好了,,,khds
21,翻身,XA\41krc\n,小意思,,,krc
22,挠痒痒,XA\42kscrh\n,舒服,,,kscrh
23,刨地,XA\43kdg\n,有宝贝,,,kdg
24,闻一下,XA\44ksnf\n,这是啥,,,ksnf
25,睡觉,XA\45kwh\n,不要,,,kwh
26,想吃东西吗？,XA\46knd\n,好夜,,,knd
27,击掌,XA\47kfiv\n,夜,,,kfiv
28,后空翻,XA\48kbf\n,看好了,,,kbf
29,前空翻,XA\49kff\n,我试试,,,kff
30,握手,XA\50khsk\n,很高兴见到你,,,khsk
31,好孩子,XA\51kgdb\n,好开心,,,kgdb
32,变桌子,XA\52ktbl\n,不许动,,,ktbl
33,打拳,XA\53kbx\n,勤学苦练,,,kbx
34,跳跳,XA\54kjmp\n,起飞,,,kjmp
35,爬上去,XA\55kclup\n,我试试,,,kclup
36,跨过去,XA\56klpov\n,我试试,,,klpov
37,生气,XA\57kang\n,好气哦,,,kang
38,派拓艺,XA\58kx\n,滴,,,kx
39,立正,XA\59c\n,遵命,,,c
40,休息,XA\60d\n,好的,,,d
配置指令,冰-冰,XAA,Switch to English,切换中/英文,,
,滴-滴,XAB,切换中文,,,
,打开音效,XAC,音效 1-3-5,（打开提示音）,,
,安静点,XAD,音效 5-3-1,（关闭提示音）,,
,开始学习,XAE,嘀嘀,进入学习命令词模式,,
,结束学习,XAF,嘀嘀嘀,退出学习模式,,
,清除数据,XAG,删除成功,（删除全部学习数据）,,
,,,,,,
串口指令表,,,,,,
串口指令,"Petoi mobile app
自定义按钮*","串口返回值
（9600波特率,ASCII码)",提示音播报,说明,注释,
XAa,"X65,97",=A63,切换英语,切换中/英文,"MCU 发送串口指令给语音模块
（返回值与接收值一样）",
XAb,"X65,98",=A64,切换中文,,,
XAc,"X65,99",=A65,音效 1-3-5,（打开提示音）,,
XAd,"X65,100",=A66,音效 5-3-1,（关闭提示音）,,
XAe,"X65,101",=A67,嘀嘀,进入学习命令词模式,,
XAf,"X65,102",=A68,嘀嘀嘀,退出学习模式,,
XAg,"X65,103",=A69,删除成功,（删除全部学习数据）,,
,,,,,,
* 如果语音模块无响应，可以通过在手机应用里添加这些自定义按钮来实现配置和激活,,,,,,
手机应用自定义命令表,,,,,,
自定义命令代码,,,说明,,,
"^X65,99;!1000;X65,97;!1000;X65,98",,,"重新激活语音模块, 并切换到中文",,,
```
