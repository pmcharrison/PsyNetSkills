"""Drive the participant flow for fast local review recordings.

Run with a visible browser while `psynet debug local` is serving the experiment:

    python scripts/playwright_participant_flow.py "http://localhost:5000/ad?..."

The script intentionally uses the participant UI instead of private endpoints so
it exercises the same controls as a human participant.
"""

import argparse
import os
import re
from itertools import cycle, islice

from playwright.sync_api import TimeoutError, sync_playwright


def click_if_visible(page, name, timeout=500):
    try:
        button = page.get_by_role("button", name=re.compile(name, re.I)).first
        button.wait_for(state="visible", timeout=timeout)
        if button.is_enabled():
            button.click()
            return True
    except TimeoutError:
        return False
    return False


def enter_sequence_response(page):
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

    for label in islice(cycle(["Low", "Medium", "High"]), target_length):
        page.get_by_role("button", name=label).click()

    page.get_by_role("button", name=re.compile("^Next$", re.I)).click()


def run_flow(url, expected_trials):
    chrome_path = os.getenv("CHROME_PATH", "/usr/bin/google-chrome")
    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path=chrome_path,
            headless=False,
            args=["--no-sandbox", "--window-size=1280,720"],
        )
        page = browser.new_page(viewport={"width": 1280, "height": 720})
        page.goto(url, wait_until="domcontentloaded")

        trials_completed = 0
        for _ in range(100):
            if click_if_visible(page, "^Begin Experiment$", timeout=1000):
                continue
            if click_if_visible(page, "^Next$", timeout=500):
                continue
            if page.locator("text=/Enter \\d+ tones in order/i").first.is_visible():
                enter_sequence_response(page)
                trials_completed += 1
                continue
            if click_if_visible(page, "^Finish$", timeout=500):
                break
            page.wait_for_timeout(250)

        page.get_by_text("Thank you", exact=False).first.wait_for(
            state="visible", timeout=15_000
        )
        if trials_completed != expected_trials:
            raise AssertionError(
                f"Expected {expected_trials} trials, completed {trials_completed}."
            )
        browser.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("url", help="PsyNet participant URL")
    parser.add_argument("--expected-trials", type=int, default=4)
    args = parser.parse_args()
    run_flow(args.url, args.expected_trials)


if __name__ == "__main__":
    main()
