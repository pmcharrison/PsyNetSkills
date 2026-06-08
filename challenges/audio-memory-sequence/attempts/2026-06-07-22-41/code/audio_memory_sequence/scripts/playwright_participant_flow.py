"""Drive the participant flow for fast local review recordings.

Run with a visible browser while `psynet debug local` is serving the experiment:

    python scripts/playwright_participant_flow.py "http://localhost:5000/ad?..."
    python scripts/playwright_participant_flow.py "http://localhost:5000/ad?..." --human-time

The script intentionally uses the participant UI instead of private endpoints so
it exercises the same controls as a human participant.
"""

import argparse
import os
import re
from itertools import cycle, islice

from playwright.sync_api import TimeoutError, sync_playwright


def pause(page, seconds):
    if seconds > 0:
        page.wait_for_timeout(int(seconds * 1000))


def click_if_visible(page, name, timeout=500, delay=0.0):
    try:
        button = page.get_by_role("button", name=re.compile(name, re.I)).first
        button.wait_for(state="visible", timeout=timeout)
        if button.is_enabled():
            button.click()
            pause(page, delay)
            return True
    except TimeoutError:
        return False
    return False


def enter_sequence_response(page, action_delay, after_audio_delay, before_next_delay):
    instruction = page.locator("text=/Enter \\d+ tones in order/i").first
    instruction.wait_for(state="visible", timeout=10_000)
    match = re.search(r"Enter (\d+) tones", instruction.inner_text())
    if match is None:
        raise RuntimeError("Could not determine target sequence length.")

    target_length = int(match.group(1))
    page.get_by_role("button", name=re.compile("^Start$", re.I)).click()
    page.locator("button.sequence-recall-button:not([disabled])").first.wait_for(
        state="visible", timeout=10_000
    )
    pause(page, after_audio_delay)

    for label in islice(cycle(["Low", "Medium", "High"]), target_length):
        page.get_by_role("button", name=label).click()
        pause(page, action_delay)

    pause(page, before_next_delay)
    page.get_by_role("button", name=re.compile("^Next$", re.I)).click()
    pause(page, action_delay)


def wait_for_completion(page):
    completion_text = page.get_by_text(
        re.compile("Thank you|end of the experiment|HIT is now complete", re.I)
    ).first
    completion_text.wait_for(state="visible", timeout=15_000)


def run_flow(
    url,
    expected_trials,
    *,
    action_delay,
    page_delay,
    after_audio_delay,
    before_next_delay,
    final_delay,
):
    chrome_path = os.getenv("CHROME_PATH", "/usr/bin/google-chrome")
    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path=chrome_path,
            headless=False,
            args=[
                "--no-sandbox",
                "--window-size=1280,720",
                "--autoplay-policy=no-user-gesture-required",
            ],
        )
        page = browser.new_page(viewport={"width": 1280, "height": 720})
        page.goto(url, wait_until="domcontentloaded")
        pause(page, page_delay)

        trials_completed = 0
        finished_clicked = False
        for _ in range(100):
            if click_if_visible(
                page, "^Begin Experiment$", timeout=1000, delay=page_delay
            ):
                continue
            if page.locator("text=/Enter \\d+ tones in order/i").first.is_visible():
                pause(page, page_delay)
                enter_sequence_response(
                    page, action_delay, after_audio_delay, before_next_delay
                )
                trials_completed += 1
                continue
            if click_if_visible(page, "^Next$", timeout=500, delay=page_delay):
                continue
            if click_if_visible(page, "^Finish$", timeout=500, delay=final_delay):
                finished_clicked = True
                break
            page.wait_for_timeout(250)

        if not finished_clicked:
            wait_for_completion(page)
        if trials_completed != expected_trials:
            raise AssertionError(
                f"Expected {expected_trials} trials, completed {trials_completed}."
            )
        if not finished_clicked:
            raise AssertionError("Expected to click the final Finish button.")
        browser.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("url", help="PsyNet participant URL")
    parser.add_argument("--expected-trials", type=int, default=4)
    parser.add_argument(
        "--human-time",
        action="store_true",
        help="Use slower pacing for illustrative recordings.",
    )
    parser.add_argument(
        "--action-delay",
        type=float,
        default=None,
        help="Seconds to pause after response/action button clicks.",
    )
    parser.add_argument(
        "--page-delay",
        type=float,
        default=None,
        help="Seconds to pause after page transitions.",
    )
    parser.add_argument(
        "--after-audio-delay",
        type=float,
        default=None,
        help="Seconds to pause after playback finishes before responding.",
    )
    parser.add_argument(
        "--before-next-delay",
        type=float,
        default=None,
        help="Seconds to show the completed response before clicking Next.",
    )
    parser.add_argument(
        "--final-delay",
        type=float,
        default=None,
        help="Seconds to pause on the final page before closing.",
    )
    args = parser.parse_args()
    defaults = {
        "action_delay": 0.6 if args.human_time else 0.0,
        "page_delay": 0.9 if args.human_time else 0.0,
        "after_audio_delay": 0.6 if args.human_time else 0.0,
        "before_next_delay": 1.2 if args.human_time else 0.0,
        "final_delay": 2.0 if args.human_time else 0.0,
    }
    run_flow(
        args.url,
        args.expected_trials,
        action_delay=args.action_delay
        if args.action_delay is not None
        else defaults["action_delay"],
        page_delay=args.page_delay
        if args.page_delay is not None
        else defaults["page_delay"],
        after_audio_delay=args.after_audio_delay
        if args.after_audio_delay is not None
        else defaults["after_audio_delay"],
        before_next_delay=args.before_next_delay
        if args.before_next_delay is not None
        else defaults["before_next_delay"],
        final_delay=args.final_delay
        if args.final_delay is not None
        else defaults["final_delay"],
    )


if __name__ == "__main__":
    main()
