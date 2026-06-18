import sys
import time
from pathlib import Path

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from psynet.testing.chrome_driver import create_psynet_chrome_driver


LOG_PATH = Path(__file__).with_name("participant-flow.log")
PARTICIPANT_URL = "http://127.0.0.1:5000/ad?generate_tokens=true&recruiter=hotair"


def xpath_literal(text):
    if "'" not in text:
        return f"'{text}'"
    if '"' not in text:
        return f'"{text}"'
    parts = text.split("'")
    return "concat(" + ', "\"\'\"", '.join(f"'{part}'" for part in parts) + ")"


def log(message):
    print(message, flush=True)
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(f"{message}\n")


def click_button(wait, label):
    label_literal = xpath_literal(label)
    xpath = (
        f"//button[normalize-space()={label_literal}] | "
        f"//input[@type='submit' and @value={label_literal}] | "
        f"//a[normalize-space()={label_literal}]"
    )
    element = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
    element.click()
    log(f"clicked: {label}")


def click_text(wait, label):
    label_literal = xpath_literal(label)
    element = wait.until(
        EC.element_to_be_clickable(
            (
                By.XPATH,
                f"//*[self::button or self::label or self::span or self::div]"
                f"[normalize-space()={label_literal}]",
            )
        )
    )
    element.click()
    log(f"selected: {label}")


def wait_for_text(wait, text):
    wait.until(EC.text_to_be_present_in_element((By.TAG_NAME, "body"), text))
    log(f"saw: {text}")


def log_page_state(driver, label):
    body = driver.find_element(By.TAG_NAME, "body").text
    log(f"{label} url: {driver.current_url}")
    log(f"{label} body: {body[:500].replace(chr(10), ' | ')}")


def switch_to_newest_window(driver):
    time.sleep(1)
    driver.switch_to.window(driver.window_handles[-1])
    log(f"switched to window: {driver.current_url}")


def click_next(wait):
    driver = wait._driver
    for label in ["Next", "Continue", "Submit"]:
        try:
            click_button(wait, label)
            return
        except Exception:
            continue
    try:
        element = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#next-button")))
        element.click()
        log("clicked: #next-button")
        return
    except Exception:
        pass
    try:
        driver.execute_script("psynet.nextPage();")
        log("advanced via psynet.nextPage()")
        time.sleep(0.5)
        return
    except Exception:
        pass
    raise RuntimeError("Could not find a next/continue/submit button")


def click_if_available(driver, label, timeout=3):
    short_wait = WebDriverWait(driver, timeout)
    try:
        click_button(short_wait, label)
        return True
    except Exception:
        return False


def choose(wait, label):
    click_text(wait, label)
    time.sleep(0.8)
    log("choice submitted")


def main():
    LOG_PATH.write_text("", encoding="utf-8")
    driver = create_psynet_chrome_driver(headless=False)
    wait = WebDriverWait(driver, 20)
    driver.set_window_size(1280, 720)

    try:
        log(f"opening: {PARTICIPANT_URL}")
        driver.get(PARTICIPANT_URL)
        wait_for_text(wait, "Thanks for your interest")
        click_button(wait, "Begin Experiment")
        switch_to_newest_window(driver)
        log_page_state(driver, "after begin")

        click_if_available(driver, "Next")
        click_if_available(driver, "I agree")

        wait_for_text(wait, "Repeated Prisoner's Dilemma")
        time.sleep(1)
        click_next(wait)

        wait_for_text(wait, "Quick check")
        choose(wait, "Copy my previous choice")

        choices = ["Cooperate", "Defect", "Cooperate", "Cooperate", "Defect", "Cooperate"]
        for index, choice in enumerate(choices, start=1):
            wait_for_text(wait, f"Round {index} of 6")
            time.sleep(0.4)
            choose(wait, choice)
            wait_for_text(wait, f"Round {index} feedback")
            time.sleep(0.8)
            click_next(wait)

        wait_for_text(wait, "Game complete")
        wait_for_text(wait, "Final score: you 16, Alex 16.")
        time.sleep(1)
        click_next(wait)
        time.sleep(2)
        log_page_state(driver, "after final submit")
        click_if_available(driver, "Finish", timeout=5)
        time.sleep(1)
        log_page_state(driver, "after finish")
        log("participant flow completed")
        time.sleep(2)
    finally:
        driver.quit()


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        log(f"participant flow failed: {exc}")
        raise
