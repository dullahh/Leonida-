# G4 failure log

Base:4e154fa1c76fd0be4f1bc575e6e52231c09c464a. Failures are recorded before changes.

1. Initial in-process asynchronous browser harness: Pause replay locator timed out after Play; Windows media-disconnect callbacks and asyncio debug slow-callback logs appeared. Other initial recovery/speed/missing-quote tests passed. The unittest runner enables asyncio debug by default, unlike the application launch. First isolate the harness overhead by disabling debug for the verification event loop and rerun only the browser case. No production fix justified yet.

Resolution: disabled asyncio debug in the test harness, matching normal runtime launch. Smallest browser-only rerun passed. Final six-test G4 run also passed with browser console-error capture, reconnect, REST fallback and reset checks. No production code change was required. Windows Proactor connection-reset/resource warnings and Uvicorn graceful-close timeout logging remain visible during browser media teardown; they are documented limitations, not suppressed or presented as clean server logs. All assertions and isolated DB cleanup completed.
