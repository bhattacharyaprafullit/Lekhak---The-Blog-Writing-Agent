"""
ui/tabs/social_tab.py
---------------------
Renders the "Social Media" tab: Twitter thread, LinkedIn post, and newsletter.

Each content type is editable inline and has its own download button so the
user can copy-paste directly into their platform of choice.
"""

import streamlit as st


def render_social_tab(out: dict) -> None:
    st.subheader("Social Media Content")
    social = out.get("social_media") or {}

    if not social:
        st.info("No social media content generated yet.")
        return

    # ---- Twitter Thread ----
    st.markdown("### Twitter Thread")
    twitter_thread = social.get("twitter_thread", [])

    if twitter_thread:
        for i, tweet in enumerate(twitter_thread, 1):
            st.text_area(
                f"Tweet {i}  —  {len(tweet)}/280 chars",
                value=tweet,
                height=80,
                key=f"tweet_{i}",
            )

        full_thread = "\n\n".join(
            [f"{i + 1}/ {t}" for i, t in enumerate(twitter_thread)]
        )
        st.download_button(
            "Download Twitter Thread",
            data=full_thread,
            file_name="twitter_thread.txt",
            mime="text/plain",
        )
    else:
        st.info("No tweets generated.")

    st.divider()

    # ---- LinkedIn Post ----
    st.markdown("### LinkedIn Post")
    linkedin = social.get("linkedin_post", "")
    edited_linkedin = st.text_area(
        f"LinkedIn Post  —  {len(linkedin)} chars",
        value=linkedin,
        height=150,
        key="linkedin_area",
    )
    st.download_button(
        "Download LinkedIn Post",
        data=edited_linkedin,
        file_name="linkedin_post.txt",
        mime="text/plain",
    )

    st.divider()

    # ---- Newsletter ----
    st.markdown("### Newsletter")
    newsletter = social.get("newsletter", "")
    edited_newsletter = st.text_area(
        "Newsletter",
        value=newsletter,
        height=150,
        key="newsletter_area",
    )
    st.download_button(
        "Download Newsletter",
        data=edited_newsletter,
        file_name="newsletter.txt",
        mime="text/plain",
    )
