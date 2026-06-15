import shutil
import subprocess
import textwrap
from pathlib import Path

import pytest


def test_action_copy_shortcut_works_from_focused_checkbox(tmp_path: Path) -> None:
    """The keyboard shortcut should work after selecting an action checkbox."""

    node = shutil.which("node")
    if node is None:
        pytest.skip("Node.js is required for the action-copy JavaScript regression test")

    script = tmp_path / "test-actions-copy.js"
    script.write_text(
        textwrap.dedent(
            """
            const fs = require("fs");
            const vm = require("vm");

            class TestEvent {
              constructor(type, options = {}) {
                this.type = type;
                this.key = options.key || "";
                this.metaKey = Boolean(options.metaKey);
                this.ctrlKey = Boolean(options.ctrlKey);
                this.altKey = Boolean(options.altKey);
                this.bubbles = Boolean(options.bubbles);
                this.defaultPrevented = false;
                this.target = null;
              }

              preventDefault() {
                this.defaultPrevented = true;
              }
            }

            class TestElement {
              constructor(tagName, attributes = {}) {
                this.tagName = tagName.toUpperCase();
                this.attributes = { ...attributes };
                this.children = [];
                this.parent = null;
                this.listeners = {};
                this.checked = false;
                this.disabled = false;
                this.hidden = false;
                this.textContent = attributes.textContent || "";
                this.value = attributes.value || "";
                this.type = attributes.type || "";
                this.style = {};
              }

              appendChild(child) {
                child.parent = this;
                this.children.push(child);
              }

              removeChild(child) {
                this.children = this.children.filter((item) => item !== child);
              }

              setAttribute(name, value) {
                this.attributes[name] = value;
              }

              getAttribute(name) {
                return this.attributes[name] || null;
              }

              select() {}

              addEventListener(type, listener) {
                this.listeners[type] = this.listeners[type] || [];
                this.listeners[type].push(listener);
              }

              dispatchEvent(event) {
                event.target = event.target || this;
                for (const listener of this.listeners[event.type] || []) {
                  listener(event);
                }
                if (event.bubbles && this.parent) {
                  this.parent.dispatchEvent(event);
                }
              }

              matches(selector) {
                if (selector === this.tagName.toLowerCase()) {
                  return true;
                }
                if (selector === "[contenteditable='']") {
                  return this.attributes.contenteditable === "";
                }
                if (selector === "[contenteditable='true']") {
                  return this.attributes.contenteditable === "true";
                }
                return false;
              }

              closest(selector) {
                const selectors = selector.split(",").map((item) => item.trim());
                let node = this;
                while (node) {
                  if (node.matches && selectors.some((item) => node.matches(item))) {
                    return node;
                  }
                  node = node.parent;
                }
                return null;
              }

              querySelector(selector) {
                if (selector === "[data-action-copy-checkbox]") {
                  return this.children.find((child) => child.attributes["data-action-copy-checkbox"] !== undefined) || null;
                }
                if (selector === ".action-card-proposal") {
                  return this.children.find((child) => child.attributes.class === "action-card-proposal") || null;
                }
                return null;
              }
            }

            class TestDocument {
              constructor(elements) {
                this.elements = elements;
                this.listeners = {};
                this.body = new TestElement("body");
              }

              getElementById(id) {
                return this.elements[id] || null;
              }

              querySelector(selector) {
                return this.elements[selector] || null;
              }

              querySelectorAll(selector) {
                if (selector === "[data-action-copy-checkbox]") {
                  return this.elements.checkboxes;
                }
                if (selector === "[data-action-card-row]") {
                  return this.elements.rows;
                }
                if (selector === ".learning-action") {
                  return [];
                }
                return [];
              }

              createElement(tagName) {
                return new TestElement(tagName);
              }

              addEventListener(type, listener) {
                this.listeners[type] = this.listeners[type] || [];
                this.listeners[type].push(listener);
              }

              dispatchEvent(event) {
                for (const listener of this.listeners[event.type] || []) {
                  listener(event);
                }
              }
            }

            const actions = [
              {
                id: "action-one",
                source_section: "First learning",
                challenge_title: "Challenge A",
                attempt_name: "attempt-1",
                source_path: "LEARNINGS.md",
                source_url: "/one",
                repository: "psynetskills",
                confidence: "high",
                impact: "high",
                status: "considering",
                learning_context: "Context one",
                proposal: "Fix action one",
                copy_context: {},
              },
              {
                id: "action-two",
                source_section: "Second learning",
                challenge_title: "Challenge B",
                attempt_name: "attempt-2",
                source_path: "LEARNINGS.md",
                source_url: "/two",
                repository: "psynet",
                confidence: "medium",
                impact: "low",
                status: "considering",
                learning_context: "Context two",
                proposal: "Fix action two",
                copy_context: {},
              },
            ];

            const dataElement = new TestElement("script", { textContent: JSON.stringify(actions) });
            const checkboxOne = new TestElement("input", { type: "checkbox", value: "action-one", "data-action-copy-checkbox": "" });
            const checkboxTwo = new TestElement("input", { type: "checkbox", value: "action-two", "data-action-copy-checkbox": "" });
            const rowOne = new TestElement("div", { "data-action-card-row": "" });
            rowOne.appendChild(checkboxOne);
            rowOne.appendChild(new TestElement("p", { class: "action-card-proposal", textContent: "Fix action one" }));
            const rowTwo = new TestElement("div", { "data-action-card-row": "" });
            rowTwo.appendChild(checkboxTwo);
            rowTwo.appendChild(new TestElement("p", { class: "action-card-proposal", textContent: "Fix action two" }));

            const elements = {
              "action-copy-data": dataElement,
              "[data-action-copy-toolbar]": new TestElement("div"),
              "[data-action-copy-count]": new TestElement("span"),
              "[data-action-copy-button]": new TestElement("button"),
              "[data-action-preview-button]": new TestElement("button"),
              "[data-action-preview-popover]": new TestElement("div"),
              "[data-action-preview-text]": new TestElement("pre"),
              "[data-action-preview-close]": new TestElement("button"),
              "[data-action-deselect-button]": new TestElement("button"),
              "[data-action-copy-status]": new TestElement("span"),
              checkboxes: [checkboxOne, checkboxTwo],
              rows: [rowOne, rowTwo],
            };
            const document = new TestDocument(elements);
            checkboxOne.parent = document;
            checkboxTwo.parent = document;

            let copiedText = "";
            const context = {
              console,
              document,
              Element: TestElement,
              Event: TestEvent,
              KeyboardEvent: TestEvent,
              Map,
              navigator: {
                clipboard: {
                  writeText: async (text) => {
                    copiedText = text;
                  },
                },
              },
              Promise,
              Set,
              setTimeout,
              URL,
              window: {
                getSelection: () => ({ isCollapsed: true, toString: () => "" }),
                isSecureContext: true,
                location: { origin: "https://example.test" },
              },
            };
            context.window.navigator = context.navigator;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync(process.argv[2], "utf8"), context);

            checkboxOne.checked = true;
            checkboxOne.dispatchEvent(new TestEvent("change", { bubbles: true }));
            checkboxOne.dispatchEvent(new TestEvent("keydown", { key: "c", metaKey: true, bubbles: true }));

            setTimeout(() => {
              if (!copiedText.includes("Action ID: action-one")) {
                throw new Error("Focused checkbox shortcut did not copy the selected action.");
              }
              if (!copiedText.includes("## Fix action one")) {
                throw new Error("Focused checkbox shortcut did not use the action point as the heading.");
              }
              if (!copiedText.includes("Impact: high")) {
                throw new Error("Focused checkbox shortcut did not copy the action impact.");
              }
              if (copiedText.includes("Action point:")) {
                throw new Error("Focused checkbox shortcut duplicated the action point text.");
              }
              if (copiedText.includes("Action ID: action-two")) {
                throw new Error("Focused checkbox shortcut copied an unselected action.");
              }
            }, 0);
            """
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [node, str(script), "dashboard/static/js/actions-copy.js"],
        cwd=Path(__file__).parent.parent,
        capture_output=True,
        text=True,
        timeout=5,
    )

    assert result.returncode == 0, result.stderr
