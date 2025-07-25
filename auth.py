 -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
Authentication System - auth.py
==============================

Simple but secure authentication system for the trading bot dashboard.
Supports password-based login with session management.
"""

import os
import streamlit as st
import hashlib
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any


class AuthSystem:
    """Simple authentication system for the trading bot"""

    def __init__(self):
        self.session_timeout = 60 * 60 * 8  # 8 hours
        self.max_login_attempts = 5
        self.lockout_duration = 300  # 5 minutes

        # Get credentials from Railway environment
        self.admin_password = os.getenv("DASHBOARD_PASSWORD", "bottie")
        self.admin_username = os.getenv("DASHBOARD_USERNAME", "admin")

        # Initialize session state
        if "authenticated" not in st.session_state:
            st.session_state.authenticated = False
        if "login_time" not in st.session_state:
            st.session_state.login_time = None
        if "login_attempts" not in st.session_state:
            st.session_state.login_attempts = 0
        if "last_attempt_time" not in st.session_state:
            st.session_state.last_attempt_time = None

    def hash_password(self, password: str) -> str:
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()

    def check_session_timeout(self) -> bool:
        """Check if session has timed out"""
        if not st.session_state.login_time:
            return True

        time_elapsed = time.time() - st.session_state.login_time
        return time_elapsed > self.session_timeout

    def is_locked_out(self) -> bool:
        """Check if user is locked out due to failed attempts"""
        if st.session_state.login_attempts < self.max_login_attempts:
            return False

        if not st.session_state.last_attempt_time:
            return False

        time_since_last_attempt = time.time() - st.session_state.last_attempt_time
        return time_since_last_attempt < self.lockout_duration

    def authenticate(self, username: str, password: str) -> bool:
        """Authenticate user credentials"""
        # Check lockout
        if self.is_locked_out():
            return False

        # Verify credentials
        is_valid = username == self.admin_username and password == self.admin_password

        if is_valid:
            # Reset attempts on successful login
            st.session_state.login_attempts = 0
            st.session_state.login_time = time.time()
            st.session_state.authenticated = True
            return True
        else:
            # Increment failed attempts
            st.session_state.login_attempts += 1
            st.session_state.last_attempt_time = time.time()
            return False

    def logout(self):
        """Logout user"""
        st.session_state.authenticated = False
        st.session_state.login_time = None

    def is_authenticated(self) -> bool:
        """Check if user is authenticated and session is valid"""
        if not st.session_state.authenticated:
            return False

        if self.check_session_timeout():
            self.logout()
            return False

        return True

    def get_lockout_time_remaining(self) -> int:
        """Get remaining lockout time in seconds"""
        if not self.is_locked_out():
            return 0

        time_since_last_attempt = time.time() - st.session_state.last_attempt_time
        return max(0, self.lockout_duration - int(time_since_last_attempt))

    def render_login_form(self) -> bool:
        """Render login form and handle authentication"""
        st.title("ðŸ” Trading Bot Login")
        st.markdown("---")

        # Check lockout
        if self.is_locked_out():
            lockout_time = self.get_lockout_time_remaining()
            st.error(
                f"ðŸš« Too many failed attempts. Try again in {lockout_time} seconds."
            )
            st.stop()

        # Show failed attempts warning
        if st.session_state.login_attempts > 0:
            remaining_attempts = (
                self.max_login_attempts - st.session_state.login_attempts
            )
            st.warning(
                f"âš ï¸ {st.session_state.login_attempts} failed attempts. {remaining_attempts} remaining."
            )

        # Login form
        with st.form("login_form"):
            col1, col2, col3 = st.columns([1, 2, 1])

            with col2:
                st.subheader("ðŸ¤– Bot Access")
                username = st.text_input("ðŸ‘¤ Username", value="admin")
                password = st.text_input("ðŸ”‘ Password", type="password")
                submit_button = st.form_submit_button(
                    "ðŸš€ Login", use_container_width=True
                )

                if submit_button:
                    if not username or not password:
                        st.error("❌ Please enter both username and password")
                        return False

                    if self.authenticate(username, password):
                        st.success("✔️ Login successful! Redirecting...")
                        time.sleep(1)
                        st.rerun()
                        return True
                    else:
                        st.error("❌ Invalid credentials")
                        time.sleep(1)
                        st.rerun()
                        return False

        # Show system info
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            st.info(
                "ðŸ›¡ï¸ **Security Features:**\n- Session timeout: 8 hours\n- Max attempts: 5\n- Lockout: 5 minutes"
            )
        with col2:
            st.info(
                "ðŸš€ **Railway Deployment:**\n- Live trading enabled\n- Real-time monitoring\n- Auto-notifications"
            )

        return False

    def render_logout_button(self):
        """Render logout button in sidebar"""
        with st.sidebar:
            st.markdown("---")
            if st.button("ðŸšª Logout", use_container_width=True):
                self.logout()
                st.success("ðŸ‘‹ Logged out successfully")
                time.sleep(1)
                st.rerun()

            # Show session info
            if st.session_state.login_time:
                login_time = datetime.fromtimestamp(st.session_state.login_time)
                st.caption(f"ðŸ• Logged in: {login_time.strftime('%H:%M:%S')}")

                time_elapsed = time.time() - st.session_state.login_time
                hours, remainder = divmod(int(time_elapsed), 3600)
                minutes, seconds = divmod(remainder, 60)
                st.caption(f"â±ï¸ Session: {hours:02d}:{minutes:02d}:{seconds:02d}")


def require_authentication():
    """Decorator-like function to require authentication"""
    auth = AuthSystem()

    if not auth.is_authenticated():
        # Show login form
        auth.render_login_form()
        st.stop()
    else:
        # Show logout button
        auth.render_logout_button()
        return auth


# Example usage in hybrid_bot.py:
# from auth import require_authentication
#
# # Add this at the top of your main app, before any content
# auth = require_authentication()
#
# # Rest of your app code continues normally...

