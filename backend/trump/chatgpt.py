import zai
print("zai version:", zai.__version__)

from zai import ZhipuAiClient

# 初始化客户端
client = ZhipuAiClient(api_key="59bec590a9174c5d9d0b57aaf8e3aecd.MkYPI9ZuWOqrRrWP")

# 特朗普的发言（你可以改成实时爬到的内容）
trump_speech = """
Some very strange things are happening in China! They are becoming very hostile, and sending letters to Countries throughout the World, that they want to impose Export Controls on each and every element of production having to do with Rare Earths, and virtually anything else they can think of, even if it’s not manufactured in China. Nobody has ever seen anything like this but, essentially, it would “clog” the Markets, and make life difficult for virtually every Country in the World, especially for China. We have been contacted by other Countries who are extremely angry at this great Trade hostility, which came out of nowhere. Our relationship with China over the past six months has been a very good one, thereby making this move on Trade an even more surprising one. I have always felt that they’ve been lying in wait, and now, as usual, I have been proven right! There is no way that China should be allowed to hold the World “captive,” but that seems to have been their plan for quite some time, starting with the “Magnets” and, other Elements that they have quietly amassed into somewhat of a Monopoly position, a rather sinister and hostile move, to say the least. But the U.S. has Monopoly positions also, much stronger and more far reaching than China’s. I have just not chosen to use them, there was never a reason for me to do so — UNTIL NOW! The letter they sent is many pages long, and details, with great specificity, each and every Element that they want to withhold from other Nations. Things that were routine are no longer routine at all. I have not spoken to President Xi because there was no reason to do so. This was a real surprise, not only to me, but to all the Leaders of the Free World. I was to meet President Xi in two weeks, at APEC, in South Korea, but now there seems to be no reason to do so. The Chinese letters were especially inappropriate in that this was the Day that, after three thousand years of bedlam and fighting, there is PEACE IN THE MIDDLE EAST. I wonder if that timing was coincidental? Dependent on what China says about the hostile “order” that they have just put out, I will be forced, as President of the United States of America, to financially counter their move. For every Element that they have been able to monopolize, we have two. I never thought it would come to this but perhaps, as with all things, the time has come. Ultimately, though potentially painful, it will be a very good thing, in the end, for the U.S.A. One of the Policies that we are calculating at this moment is a massive increase of Tariffs on Chinese products coming into the United States of America. There are many other countermeasures that are, likewise, under serious consideration. Thank you for your attention to this matter!
"""

# 创建聊天请求
response = client.chat.completions.create(
    model="GLM-4.6",
    messages=[
        {
            "role": "system",
            "content": (
                "你是一个专业的政治与金融分析师，擅长分析特朗普的发言对股市的影响。"
                "请严格按照以下格式输出结果：\n\n"
                "【主题】：简述发言的主要内容\n"
                "【情绪】：判断整体情绪（乐观、积极、愤怒、威胁、焦虑、悲观等）\n"
                "【股市潜在影响】：对币圈、美股的影响 \n"
                "【总结】: 20字以内的总结，按星级总结整体市场影响倾向（利好/利空/中性）,总星是5星。 如果利好，那么就是星级越多越好。如果利空，那么星级越多越利空。"
            )
        },
        {
            "role": "user",
            "content": f"特朗普最新发言如下：\n{trump_speech}\n请按上述格式分析。"
        }
    ],
    temperature=0.5
)

# 输出模型分析结果
print(response.choices[0].message.content)
