import pytest
from utils.email_alerts import EmailAlerter
import os
from unittest.mock import patch, MagicMock

@pytest.fixture
def email_config(monkeypatch):
    """Setup test email configuration"""
    monkeypatch.setenv("ALERT_EMAIL", "test@example.com")
    monkeypatch.setenv("ALERT_EMAIL_PASSWORD", "test_password")
    monkeypatch.setenv("RECIPIENT_EMAIL", "recipient@example.com")
    return {
        "sender": "test@example.com",
        "password": "test_password",
        "recipient": "recipient@example.com"
    }

@pytest.fixture
def sample_changes():
    """Sample change data for testing"""
    return [{
        'url': 'https://books.toscrape.com/test-book',
        'title': 'Test Book',
        'type': 'price_change',
        'changes': {
            'price_including_tax': {'old': '10.99', 'new': '8.99'},
            'availability': {'old': 'In stock', 'new': 'Out of stock'}
        }
    }]

def test_email_alerter_initialization(email_config):
    """Test EmailAlerter initialization with config"""
    alerter = EmailAlerter()
    assert alerter.sender_email == email_config["sender"]
    assert alerter.sender_password == email_config["password"]
    assert alerter.recipient_email == email_config["recipient"]

@pytest.mark.parametrize("missing_env", ["ALERT_EMAIL", "ALERT_EMAIL_PASSWORD", "RECIPIENT_EMAIL"])
def test_email_alerter_missing_config(monkeypatch, missing_env):
    """Test EmailAlerter behavior with missing configuration"""
    # Clear the specific environment variable
    monkeypatch.delenv(missing_env, raising=False)
    
    alerter = EmailAlerter()
    result = alerter.send_alert("Test", [])
    assert result is False

@patch('smtplib.SMTP')
def test_send_alert_success(mock_smtp, email_config, sample_changes):
    """Test successful email alert sending"""
    # Setup mock
    mock_server = MagicMock()
    mock_smtp.return_value.__enter__.return_value = mock_server

    alerter = EmailAlerter()
    result = alerter.send_alert("Test Alert", sample_changes)

    # Verify
    assert result is True
    mock_server.starttls.assert_called_once()
    mock_server.login.assert_called_once_with(email_config["sender"], email_config["password"])
    assert mock_server.send_message.called

@patch('smtplib.SMTP')
def test_send_alert_smtp_error(mock_smtp, email_config, sample_changes):
    """Test email alert sending with SMTP error"""
    # Setup mock to raise an exception
    mock_smtp.return_value.__enter__.side_effect = Exception("SMTP Error")

    alerter = EmailAlerter()
    result = alerter.send_alert("Test Alert", sample_changes)

    # Verify
    assert result is False

def test_email_content_formatting(email_config, sample_changes):
    """Test email content formatting"""
    alerter = EmailAlerter()
    html_content = alerter._format_changes_html(sample_changes)

    # Verify content includes key information
    assert 'Test Book' in html_content
    assert 'price_change' in html_content
    assert '10.99' in html_content
    assert '8.99' in html_content
    assert 'table' in html_content
    assert 'tr' in html_content

def test_changes_details_formatting(email_config):
    """Test change details formatting"""
    alerter = EmailAlerter()
    details = {
        'price': {'old': '£10.99', 'new': '£8.99'},
        'status': 'updated'
    }
    
    formatted = alerter._format_changes_details(details)
    assert 'price' in formatted
    assert '£10.99' in formatted
    assert '£8.99' in formatted
    assert 'status' in formatted
    assert 'updated' in formatted