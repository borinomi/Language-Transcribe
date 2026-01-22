import re

def srt_time_to_ms(t):
    # 00:01:23,456 → ms
    h, m, rest = t.split(':')
    s, ms = rest.split(',')

    return (
        int(h) * 3600000 +
        int(m) * 60000 +
        int(s) * 1000 +
        int(ms)
    )


def parse_srt(path):
    subs = []
    texts = []

    with open(path, 'r', encoding='utf-8') as f:
        blocks = f.read().strip().split('\n\n')

    for block in blocks:
        lines = block.splitlines()
        if len(lines) < 3:
            continue

        time_line = lines[1]
        text = " ".join(lines[2:]).strip()

        start, end = time_line.split(' --> ')
        subs.append({
            'begin': srt_time_to_ms(start),
            'end': srt_time_to_ms(end)
        })
        texts.append(text)

    return subs, texts
