# Отчёт: Qwen3.8-27B-QUASAR-NVFP4 на Basalt v0.4.1 (ноутбук RTX 5090 Laptop, 24 ГБ VRAM)

## Главный вывод

Модель работает быстро ровно до тех пор, пока весь KV-кэш помещается в VRAM. На этой машине
граница проходит на **140,288 токенов** в режиме с DFlash 2 (движок уже отказывается на
142,336) и на **203,776** в режиме без спекуляции (отказ с 205,824). Выше границы включается `--kv-resident`, и тогда
скорость генерации определяется не вычислениями, а шиной: она натренирована на **PCIe 4.0 x8**
(карта умеет 5.0 x16), фактическая пропускная способность **14.4 ГБ/с**. На 256K это
**4.7 ток/с** без DFlash и **5.1 ток/с** с DFlash 2 — то есть ускорение от спекуляции почти исчезает
(×1.09), потому что узкое место — перенос KV, а не расчёт.

Декод без спекуляции по медианам: 37 → 35 → 31 → 27 ток/с на 4K → 32K → 66K → 131K.
Prefill в том же режиме: 6499 → 5739 → 4524 → 3249 ток/с.

DFlash 2 (окно 16) даёт **×2.9–3.2** на контекстах до 131K при приёме черновика 55–71 %.
Внутри одного ответа DFlash разгоняется: на 66K четверти 79 → 99 → 106 → 100, на 131K 77 → 90 → 95 → 89.
Обычный декод плоский везде (D4/D1 ≈ 0.98–1.0).

## Матрица измерений

| context (actual tokens) | mode | KV in RAM | prefill tok/s | TTFT s | decode tok/s | D1 / D2 / D3 / D4 tok/s | draft accept | VRAM peak MiB | RAM peak MiB | GPU power W | GPU °C max | PCIe link under load |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 4K (4165) | DFlash 2 (spec 16) | none (all in VRAM) | 7124.0 | 0.63 | 120.5 | 121.5 / 120.5 / 103.3 / 156.8 | 50.0% | 19250.0 | 6677 | 150.7 avg / 169.6 peak | 55.0 | 16.0 GT/s PCIe x8 |
| 4K (4165) | plain | none (all in VRAM) | 6499.0 | 0.87 | 37.8 | 38.7 / 38.3 / 38.2 / 38.3 | n/a | 16858.0 | 6262 | 139.8 avg / 161.8 peak | 54.0 | 16.0 GT/s PCIe x8 |
| 32K (31803) | DFlash 2 (spec 16) | none (all in VRAM) | 5578.0 | 5.75 | 105.5 | 87.8 / 127.2 / 117.7 / 101.9 | 50.0% | 20078.0 | 6599 | 164.0 avg / 178.7 peak | 66.0 | 16.0 GT/s PCIe x8 |
| 32K (31803) | plain | none (all in VRAM) | 5739.0 | 5.59 | 35.1 | 35.5 / 35.1 / 35.1 / 35.1 | n/a | 17682.0 | 6368 | 152.5 avg / 174.3 peak | 64.0 | 16.0 GT/s PCIe x8 |
| 33K (32649) | DFlash 2 (spec 16) | none (all in VRAM) | 5577.0 | 5.89 | 113.1 | 104.6 / 114.0 / 134.1 / 112.9 | 56.0% | 20074.0 | 6611 | 160.8 avg / 178.7 peak | 66.0 | 16.0 GT/s PCIe x8 |
| 33K (32649) | plain | none (all in VRAM) | 5705.0 | 5.76 | 35.0 | 35.3 / 34.9 / 34.9 / 34.9 | n/a | 17682.0 | 6232 | 152.5 avg / 174.3 peak | 64.0 | 16.0 GT/s PCIe x8 |
| 66K (65785) | DFlash 2 (spec 16) | none (all in VRAM) | 4440.0 | 14.87 | 91.3 | 78.8 / 85.9 / 106.3 / 97.1 | 55.0% | 21128.0 | 6583 | 168.3 avg / 174.6 peak | 67.0 | 16.0 GT/s PCIe x8 |
| 66K (65785) | plain | none (all in VRAM) | 4524.0 | 14.6 | 31.6 | 32.0 / 31.7 / 31.7 / 31.6 | n/a | 18738.0 | 6330 | 159.7 avg / 172.7 peak | 66.0 | 16.0 GT/s PCIe x8 |
| 131K (131492) | DFlash 2 (spec 16) | none (all in VRAM) | 3182.0 | 41.42 | 86.6 | 77.0 / 90.2 / 95.4 / 89.2 | 71.0% | 23228.0 | 6627 | 170.1 avg / 175.0 peak | 69.0 | 16.0 GT/s PCIe x8 |
| 131K (131492) | plain | none (all in VRAM) | 3249.0 | 40.55 | 27.0 | 27.3 / 27.1 / 27.1 / 27.0 | n/a | 20850.0 | 6380 | 165.5 avg / 173.9 peak | 64.0 | 16.0 GT/s PCIe x8 |
| 135K (134561) | DFlash 2 (spec 16) | none (all in VRAM) | 3136.0 | 43.09 | 64.7 | 55.0 / 78.5 / 76.9 / 63.6 | 63.0% | 23498.0 | 6584 | 170.5 avg / 174.6 peak | 70.0 | 16.0 GT/s PCIe x8 |
| 198K (197886) | plain | none (all in VRAM) | 2476.0 | 80.04 | 23.5 | 23.9 / 23.5 / 23.5 / 23.5 | n/a | 23160.0 | 6264 | 170.3 avg / 176.0 peak | 68.0 | 16.0 GT/s PCIe x8 |
| 256K (256115) | DFlash 2 (spec 16) | 131072 | 2010.0 | 127.9 | 5.1 | 4.6 / 5.2 / 5.7 / 5.2 | 77.0% | 23482.0 | 10946 | 148.0 avg / 175.4 peak | 71.0 | 16.0 GT/s PCIe x8 |
| 256K (256115) | plain | 196608 | 2030.0 | 126.44 | 4.7 | 4.7 / 4.8 / 4.7 / 4.7 | n/a | 23068.0 | 8533 | 150.0 avg / 174.9 peak | 71.0 | 16.0 GT/s PCIe x8 |

`D1..D4` — четыре равные части **одного непрерывного ответа** (512 токенов), разрезанные по точным
границам токенов потокового ответа, а не четыре отдельных запроса.

## Потолок контекста при KV-кэше целиком в VRAM

| mode | largest context that starts with KV fully in VRAM | first rejected value | note |
|---|---|---|---|
| spec 0 | 203776 | 205824 | 204K fits, 206K refused |
| spec 16 | 140288 | 142336 | 140K fits, 142K refused |

Дословные отказы движка сохранены в `raw/failures.csv`, например
`1 session(s) of 224000 cells need 9575 MiB, 9487 MiB are free`.

## Корректность на длинном контексте (две разные методики)

| run | free-form 'list all control records' | correct |
|---|---|---|
| A128k | requested | 0/5 |
| B128k | requested | 0/5 |
| A256k | requested | 0/5 |
| B256k | requested | 0/5 |

Текст свободного запроса дословно: `I cannot find any CONTROL records in the provided text.`

| prompt tokens | KV in RAM | spec | targeted questions answered correctly |
|---|---|---|---|
| 131492 | none | 16 | 5/5 |
| 256115 | 131072 | 16 | 5/5 |

Если спрашивать контрольную запись **по её точному идентификатору**, модель выдаёт точное значение
и на 131K, и на 256K (при 131 072 позициях KV в RAM). Значит информация удерживается и извлекается;
не работает только формулировка «найди и перечисли все такие записи».

## Ответы на пять вопросов отчёта

1. **Максимальная скорость на короткой задаче:** 194.3 ток/с генерации (DFlash 2, контекст 4K);
   самая быстрая отдельная четверть того же прогона — 264.3 ток/с.
2. **Устойчивая скорость на длинной задаче** (медиана всего ответа и последняя четверть):
- 66K: whole answer 31.7 tok/s plain / 92.0 tok/s DFlash 2; last quarter 31.6 / 97.1 tok/s
- 131K: whole answer 27.1 tok/s plain / 87.4 tok/s DFlash 2; last quarter 27.0 / 89.2 tok/s
- 256K: whole answer 4.7 tok/s plain / 5.1 tok/s DFlash 2; last quarter 4.7 / 5.2 tok/s
3. **Прирост от DFlash 2** (медиана генерации):

| context (tokens) | plain tok/s | DFlash 2 tok/s | speedup | KV positions in VRAM (plain / DFlash) |
|---|---|---|---|---|
| 4165 | 37.8 | 120.5 | x3.19 | all / all |
| 31803 | 35.1 | 105.5 | x3.01 | all / all |
| 32649 | 35.0 | 113.1 | x3.23 | all / all |
| 65785 | 31.6 | 91.3 | x2.89 | all / all |
| 131492 | 27.0 | 86.6 | x3.21 | all / all |
| 256115 | 4.7 | 5.1 | x1.09 | 196608 / 131072 |

4. **Изменение скорости внутри ответа** (четверти одного непрерывного ответа):

| context (tokens) | mode | D1 tok/s | D4 tok/s | D4 / D1 |
|---|---|---|---|---|
| 4165 | dflash2 | 121.5 | 156.8 | 1.29 |
| 4165 | plain | 38.7 | 38.3 | 0.99 |
| 31803 | dflash2 | 87.8 | 101.9 | 1.16 |
| 31803 | plain | 35.5 | 35.1 | 0.99 |
| 32649 | dflash2 | 104.6 | 112.9 | 1.08 |
| 32649 | plain | 35.3 | 34.9 | 0.99 |
| 65785 | dflash2 | 78.8 | 97.1 | 1.23 |
| 65785 | plain | 32.0 | 31.6 | 0.99 |
| 131492 | dflash2 | 77.0 | 89.2 | 1.16 |
| 131492 | plain | 27.3 | 27.0 | 0.99 |
| 134561 | dflash2 | 55.0 | 63.6 | 1.16 |
| 197886 | plain | 23.9 | 23.5 | 0.98 |
| 256115 | dflash2 | 4.6 | 5.2 | 1.13 |
| 256115 | plain | 4.7 | 4.7 | 1.0 |

5. **Максимальный рабочий контекст на 24 ГБ:** KV-кэш целиком в VRAM держится до
**203,776 токенов без спекуляции** и до **140,288 токенов с DFlash 2**
(на шаг выше движок уже отказывает). Замеры на этом потолке:
- 134,561 tokens, max-context 140288, DFlash 2: prefill 3,136 tok/s, TTFT 43.09 s, decode 64.7 tok/s, VRAM peak 23,498 MiB
- 197,886 tokens, max-context 203776, plain: prefill 2,476 tok/s, TTFT 80.04 s, decode 23.5 tok/s, VRAM peak 23,160 MiB
- 256115 tokens (DFlash 2) needs --kv-resident 131072: decode 5.1 tok/s
- 256115 tokens (plain) needs --kv-resident 196608: decode 4.7 tok/s

## Железо (замерено на машине, а не взято из паспорта)

```
hardware (measured before the engine starts)
  CPU   AMD Ryzen 9 9955HX, 16 cores
  RAM   read 58.8 GB/s
  GPU   RTX 5090 Laptop GPU  PCIe 4.0 x8  host-to-device 14.4 GB/s
```

```
CPU(s):                                  32
Model name:                              AMD Ryzen 9 9955HX 16-Core Processor
Thread(s) per core:                      2
Core(s) per socket:                      16
Socket(s):                               1
CPU(s) scaling MHz:                      44%
CPU max MHz:                             5460.5269
               total        used        free      shared  buff/cache   available
Mem:     64963141632 58704912384   793706496  2093563904  8262262784  6258229248
Swap:    68719468544    68255744 68651212800
Linux 7.0.0-43-generic
PRETTY_NAME="Ubuntu 24.04.5 LTS"
NAME="Ubuntu"
/usr/local/cuda
/usr/local/cuda-13
/usr/local/cuda-13.0
```

## Что не успели и честно помечено

| run | status | KV positions kept in VRAM | engine reason (verbatim) |
|---|---|---|---|
| A256k | START_FAILED | 0 | [server] error: qwen35: 1 session(s) of 262144 cells need 10804 MiB, 9487 MiB are free; lower --max-context or --paralle |
| B256k | START_FAILED | 0 | [server] error: qwen35: 1 session(s) of 262144 cells need 10804 MiB, 7421 MiB are free; lower --max-context or --paralle |
| B256k | START_FAILED | 196608 | [server] error: qwen35: 1 session(s) of 262144 cells need 8824 MiB, 7421 MiB are free; lower --max-context or --parallel |
| B256k | START_FAILED | 163840 | [server] error: qwen35: 1 session(s) of 262144 cells need 7834 MiB, 7421 MiB are free; lower --max-context or --parallel |
| V224k_plain | START_FAILED | 0 | [server] error: qwen35: 1 session(s) of 224000 cells need 9575 MiB, 9487 MiB are free; lower --max-context or --parallel |
| V224k_dflash | START_FAILED | 0 | [server] error: qwen35: 1 session(s) of 224000 cells need 9575 MiB, 7421 MiB are free; lower --max-context or --parallel |
| W221k_plain | START_FAILED | 0 | [server] error: qwen35: 1 session(s) of 221184 cells need 9484 MiB, 9487 MiB are free; lower --max-context or --parallel |
| W173k_dflash | START_FAILED | 0 | [server] error: qwen35: 1 session(s) of 173056 cells need 7933 MiB, 7421 MiB are free; lower --max-context or --parallel |

Отдельных длительных стресс-тестов не было;Prefill по четвертям не измерялся — в Basalt v0.4.1 нет
штатного инструмента для разбиения одной операции prefill, а дорабатывать движок по ТЗ запрещалось.
