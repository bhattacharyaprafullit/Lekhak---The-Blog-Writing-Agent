"""
nodes/social_media.py
---------------------
The Social Media node runs AFTER the reducer has assembled the final blog.

It takes the first ~1200 characters of the blog (enough context for tone and
content without blowing the token budget) and generates three content pieces:
a Twitter/X thread, a LinkedIn post, and an email newsletter.

This node is intentionally last in the graph so it always has the complete
blog text to work from.
"""

from langchain_core.messages import SystemMessage, HumanMessage

from app.core.llm import llm
from app.models.schemas import SocialMediaContent, State

SOCIAL_SYSTEM = """You are an expert social media content creator specializing in tech content.
Generate engaging, high-quality social media content based on the provided blog post.
Respond in JSON format.

Return EXACTLY this JSON structure with these EXACT field names:
{
  "twitter_thread": [
    "Tweet 1 text here",
    "Tweet 2 text here",
    "Tweet 3 text here",
    "Tweet 4 text here",
    "Tweet 5 text here",
    "Tweet 6 text here"
  ],
  "linkedin_post": "Full LinkedIn post here",
  "newsletter": "Full newsletter here"
}

TWITTER THREAD RULES:
- Write exactly 6 tweets.
- Tweet 1 must be a strong hook that makes people want to read more. Use an emoji at the start.
- Each tweet must be under 280 characters.
- Use relevant emojis naturally throughout (not forced).
- Number the tweets like: 1/ , 2/ , 3/ etc.
- Last tweet should have a call to action like "Follow for more" or "Save this thread".
- Example good tweet: "1/ Most developers are building RAG systems WRONG. Here is what nobody tells you about retrieval augmented generation. A thread."

LINKEDIN POST RULES:
- Write a full, engaging LinkedIn post between 800-1200 characters.
- Start with a strong hook line that stops the scroll.
- Use line breaks between paragraphs for readability.
- Include 2-3 key insights or takeaways from the blog.
- Use emojis as bullet points or section markers where appropriate (like checkmark, key, lightbulb, rocket).
- End with a thought-provoking question to drive comments.
- Add 5-7 relevant hashtags at the end.
- Example good opening: "Most people think they understand X. They dont. Here is what actually matters:"

NEWSLETTER RULES:
- Write a proper email newsletter between 400-600 characters.
- Include a subject line at the very top like: "Subject: <subject here>"
- Start with a friendly greeting like "Hey [First Name],"
- Write 2-3 short paragraphs covering the main points.
- Include a clear call to action at the end like "Read the full blog here: [link]"
- Keep tone conversational and friendly, not corporate.
- End with a sign-off like "Until next time," followed by a name.

GENERAL RULES:
- Use plain ASCII characters only -- no special Unicode dashes or fancy quotes.
- Make the content genuinely useful and interesting, not generic.
- Write as if you are a real person sharing something exciting they learned.
"""


def social_media_node(state: State) -> dict:
    final_md = state.get("final", "")
    plan = state.get("plan")

    if not final_md:
        return {"social_media": {}}

    # First 1200 chars gives the model enough context without wasting tokens
    blog_summary = final_md[:1200]

    generator = llm.with_structured_output(SocialMediaContent, method="json_mode")

    content = generator.invoke(
        [
            SystemMessage(content=SOCIAL_SYSTEM),
            HumanMessage(
                content=(
                    f"Blog title: {plan.blog_title if plan else 'Blog'}\n"
                    f"Blog kind: {plan.blog_kind if plan else 'explainer'}\n"
                    f"Audience: {plan.audience if plan else 'developers'}\n\n"
                    f"Blog content:\n{blog_summary}\n\n"
                    f"Now generate engaging social media content for this blog. "
                    f"Make it genuinely interesting and worth sharing."
                )
            ),
        ]
    )

    return {"social_media": content.model_dump()}
