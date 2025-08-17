#!/usr/bin/env python3
"""
Automate MCP Inspector testing by starting the inspector and parsing its output
"""

import queue
import re
import subprocess
import sys
import threading
import time
from typing import Any

import requests


class MCPInspectorClient:
    def __init__(self):
        self.inspector_url = None
        self.proxy_url = None
        self.auth_token = None
        self.inspector_process = None
        self.session = requests.Session()

    def start_inspector(self, timeout: int = 30) -> bool:
        """Start MCP Inspector and parse its output to get connection details"""
        print("🚀 Starting MCP Inspector...")

        try:
            # Start the inspector process
            self.inspector_process = subprocess.Popen(
                ["npx", "@modelcontextprotocol/inspector"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,  # Line buffered
                universal_newlines=True,
            )

            # Use a queue to collect output from the subprocess
            output_queue = queue.Queue()

            def read_output():
                for line in self.inspector_process.stdout:
                    output_queue.put(line)
                    print(f"[Inspector] {line.strip()}")

            # Start reading output in a separate thread
            output_thread = threading.Thread(target=read_output, daemon=True)
            output_thread.start()

            # Parse the output to extract connection details
            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    # Check if we have any output
                    line = output_queue.get(timeout=1)

                    # Look for proxy server port
                    proxy_match = re.search(
                        r"Proxy server listening on localhost:(\d+)", line
                    )
                    if proxy_match:
                        proxy_port = proxy_match.group(1)
                        self.proxy_url = f"http://localhost:{proxy_port}"
                        print(f"🔧 Found proxy server: {self.proxy_url}")

                    # Look for session token
                    token_match = re.search(r"Session token: ([a-f0-9]+)", line)
                    if token_match:
                        self.auth_token = token_match.group(1)
                        print(f"🔑 Found auth token: {self.auth_token[:16]}...")

                    # Look for main inspector URL
                    url_match = re.search(
                        r"http://localhost:(\d+)/\?MCP_PROXY_AUTH_TOKEN=([a-f0-9]+)",
                        line,
                    )
                    if url_match:
                        inspector_port = url_match.group(1)
                        token_from_url = url_match.group(2)
                        self.inspector_url = f"http://localhost:{inspector_port}"

                        # Use token from URL if we don't have one yet
                        if not self.auth_token:
                            self.auth_token = token_from_url

                        print(f"🌐 Found inspector URL: {self.inspector_url}")

                    # Check if we have everything we need
                    if self.inspector_url and self.proxy_url and self.auth_token:
                        print("✅ MCP Inspector started successfully!")

                        # Set up session headers
                        self.session.headers.update(
                            {
                                "Authorization": f"Bearer {self.auth_token}",
                                "MCP-Proxy-Auth-Token": self.auth_token,
                            }
                        )

                        # Wait a moment for the server to be ready
                        time.sleep(2)
                        return True

                except queue.Empty:
                    # Check if process is still running
                    if self.inspector_process.poll() is not None:
                        print("❌ Inspector process terminated unexpectedly")
                        return False
                    continue
                except Exception as e:
                    print(f"⚠️  Error parsing inspector output: {e}")
                    continue

            print("❌ Timeout waiting for inspector to start")
            return False

        except FileNotFoundError:
            print("❌ npx not found. Install Node.js and npm first:")
            print("   brew install node  # macOS")
            print("   # or visit https://nodejs.org/")
            return False
        except Exception as e:
            print(f"❌ Failed to start inspector: {e}")
            return False

    def stop_inspector(self):
        """Stop the MCP Inspector process"""
        if self.inspector_process:
            print("🛑 Stopping MCP Inspector...")
            self.inspector_process.terminate()
            try:
                self.inspector_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.inspector_process.kill()
            self.inspector_process = None

    def test_connection(self) -> bool:
        """Test if we can connect to the inspector"""
        if not all([self.inspector_url, self.proxy_url, self.auth_token]):
            print("❌ Missing connection details")
            return False

        try:
            response = self.session.get(self.inspector_url, timeout=5)
            if response.status_code == 200:
                print("✅ Connected to MCP Inspector")
                return True
            else:
                print(f"❌ Inspector responded with status {response.status_code}")
                return False

        except Exception as e:
            print(f"❌ Could not connect to inspector: {e}")
            return False

    def create_server_connection(self, server_config: dict[str, Any]) -> str | None:
        """Create a server connection through the proxy"""
        try:
            payload = {
                "transportType": server_config.get("transportType", "stdio"),
                "command": server_config.get("command"),
                "args": server_config.get("args", []),
                "env": server_config.get("env", {}),
            }

            print(f"🔌 Creating connection with config: {payload}")

            # Try different possible endpoints
            endpoints = ["/connect", "/api/connect", "/proxy/connect"]

            for endpoint in endpoints:
                try:
                    response = self.session.post(
                        f"{self.proxy_url}{endpoint}", json=payload, timeout=10
                    )

                    if response.status_code == 200:
                        result = response.json()
                        connection_id = (
                            result.get("connectionId") or result.get("id") or "default"
                        )
                        print(f"✅ Created connection: {connection_id}")
                        return connection_id
                    elif response.status_code == 404:
                        continue  # Try next endpoint
                    else:
                        print(
                            f"⚠️  Endpoint {endpoint} returned {response.status_code}: {response.text}"
                        )

                except Exception as e:
                    print(f"⚠️  Failed endpoint {endpoint}: {e}")
                    continue

            print("❌ Could not find working connection endpoint")
            return None

        except Exception as e:
            print(f"❌ Error creating connection: {e}")
            return None

    def send_mcp_message(
        self, connection_id: str, message: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Send an MCP message through the proxy"""
        try:
            # Try different possible endpoints
            endpoints = [
                f"/message/{connection_id}",
                f"/api/message/{connection_id}",
                f"/proxy/{connection_id}",
                f"/{connection_id}/message",
            ]

            for endpoint in endpoints:
                try:
                    response = self.session.post(
                        f"{self.proxy_url}{endpoint}", json=message, timeout=15
                    )

                    if response.status_code == 200:
                        return response.json()
                    elif response.status_code == 404:
                        continue  # Try next endpoint
                    else:
                        print(
                            f"⚠️  Message endpoint {endpoint} returned {response.status_code}"
                        )

                except Exception as e:
                    print(f"⚠️  Failed message endpoint {endpoint}: {e}")
                    continue

            print("❌ Could not find working message endpoint")
            return None

        except Exception as e:
            print(f"❌ Error sending message: {e}")
            return None


def main():
    """Test MCP Inspector automation by starting inspector and parsing output"""
    print("🤖 Automated MCP Inspector Testing")
    print("🚀 Starting Inspector and Auto-Detecting Configuration")
    print("=" * 60)

    client = MCPInspectorClient()

    try:
        # Start the inspector and parse its output
        if not client.start_inspector():
            print("\n❌ Failed to start MCP Inspector")
            print("\n💡 Fallback: Use the STDIO approach instead:")
            print("   python mcp_local_repo_analyzer/tests/integration/test_chain.py")
            return False

        # Test connection
        if not client.test_connection():
            print("❌ Could not connect to started inspector")
            return False

        print("\n📋 Inspector Configuration:")
        print(f"   🌐 Inspector URL: {client.inspector_url}")
        print(f"   🔧 Proxy URL: {client.proxy_url}")
        print(f"   🔑 Auth Token: {client.auth_token[:16]}...")

        # Test repository analyzer
        print("\n📊 Testing Repository Analyzer Connection...")

        repo_config = {
            "transportType": "stdio",
            "command": "poetry",
            "args": [
                "run",
                "python",
                "-m",
                "mcp_local_repo_analyzer.main",
                "--work-dir",
                "./mcp_local_repo_analyzer",
            ],
            "env": {},
        }

        repo_conn = client.create_server_connection(repo_config)
        if not repo_conn:
            print("❌ Could not create repository analyzer connection")
            print(
                "💡 This may be expected - the Inspector API might not support automation"
            )
            return False

        # If we get here, we can try to send messages
        print("✅ Connection created, testing MCP communication...")

        # Initialize
        init_message = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "automated-test", "version": "1.0.0"},
            },
        }

        init_result = client.send_mcp_message(repo_conn, init_message)
        if init_result:
            print("✅ Repository analyzer initialized via Inspector!")
            print("🎉 Inspector automation is working!")
            return True
        else:
            print("⚠️  Could not send MCP messages through Inspector")
            print("💡 The Inspector may be designed for browser use only")
            return False

    finally:
        # Always clean up
        client.stop_inspector()
        print("🧹 Cleaned up inspector process")


if __name__ == "__main__":
    success = main()

    if not success:
        print("\n" + "=" * 60)
        print("💡 RECOMMENDATION: Use the proven STDIO approach instead:")
        print("   python mcp_local_repo_analyzer/tests/integration/test_chain.py")
        print("   This is faster, more reliable, and designed for automation!")

    sys.exit(0 if success else 1)
