import argparse  # For parsing command-line arguments
import socket   # For network communication
import shlex    # For splitting command strings safely
import subprocess  # For running system commands
import sys      # For system-specific functions like stdin and exit
import textwrap  # For formatting help text
import threading  # For handling multiple client connections

# Function to execute a system command and return its output
def execute(cmd):
    """
    Executes a system command and returns its output as a string.
    Args:
        cmd (str): The command to execute.
    Returns:
        str: The output of the command, or empty string if command fails.
    """
    cmd = cmd.strip()  # Remove leading/trailing whitespace
    if not cmd:  # If command is empty, return nothing
        return ""
    try:
        # Run the command using subprocess, capturing output and errors
        output = subprocess.check_output(shlex.split(cmd), stderr=subprocess.STDOUT)
        return output.decode()  # Convert byte output to string
    except subprocess.CalledProcessError:
        return ""  # Return empty string if command fails

# NetCat class to handle network communication
class NetCat:
    def __init__(self, args, buffer=None):
        """
        Initialize NetCat object with command-line arguments and optional buffer.
        Args:
            args: Parsed command-line arguments (from argparse).
            buffer: Data to send (optional, used when not listening).
        """
        self.args = args  # Store command-line arguments
        self.buffer = buffer  # Store data to send (if any)
        # Create a TCP socket (AF_INET for IPv4, SOCK_STREAM for TCP)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Allow port reuse to avoid "address already in use" errors
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def run(self):
        """
        Main method to decide whether to listen or send based on arguments.
        """
        if self.args.listen:  # If -l flag is set, start listening
            self.listen()
        else:  # Otherwise, act as a client and send data
            self.send()

    def send(self):
        """
        Connect to a target and send/receive data interactively.
        """
        # Connect to the specified target IP and port
        self.socket.connect((self.args.target, self.args.port))
        
        # If there's a buffer (data from stdin), send it
        if self.buffer:
            self.socket.send(self.buffer)

        try:
            while True:  # Loop to receive and send data
                recv_len = 1  # Track received data length
                response = ""  # Store received data
                while recv_len:  # Keep receiving until no more data
                    data = self.socket.recv(4096)  # Receive up to 4096 bytes
                    recv_len = len(data)  # Update length
                    response += data.decode()  # Decode and append to response
                    if recv_len < 4096:  # If less than 4096 bytes, no more data
                        break
                if response:  # If we received data, print it
                    print(response)
                
                # Get user input for sending back to the server
                buffer = input("> ")  # Prompt for input
                buffer += "\n"  # Add newline for compatibility
                self.socket.send(buffer.encode())  # Send input to server
                
        except KeyboardInterrupt:  # Handle Ctrl+C to exit gracefully
            print("User terminated.")
            self.socket.close()  # Close the socket
            sys.exit()  # Exit the program
        except Exception as e:  # Handle other errors
            print(f"Error during send: {e}")
            self.socket.close()

    def listen(self):
        """
        Set up a server to listen for incoming connections and handle them.
        """
        # Bind the socket to the target IP and port
        self.socket.bind((self.args.target, self.args.port))
        self.socket.listen(5)  # Listen for up to 5 queued connections
        
        while True:  # Keep accepting new connections
            try:
                # Accept a client connection (returns socket and address)
                client_socket, _ = self.socket.accept()
                # Create a new thread to handle the client
                client_thread = threading.Thread(
                    target=self.handle, args=(client_socket,)
                )
                client_thread.start()  # Start the thread
            except Exception as e:
                print(f"Error in listen: {e}")
                break
        self.socket.close()  # Close the server socket if loop breaks

    def handle(self, client_socket):
        """
        Handle client connections based on command-line arguments.
        Args:
            client_socket: The socket object for the connected client.
        """
        if self.args.execute:  # If -e flag is set, execute a command
            output = execute(self.args.execute)  # Run the specified command
            client_socket.send(output.encode())  # Send output to client
            
        elif self.args.upload:  # If -u flag is set, receive and save a file
            file_buffer = b""  # Buffer to store file data
            while True:
                data = client_socket.recv(4096)  # Receive file data
                if data:  # If data is received, append to buffer
                    file_buffer += data
                else:  # No more data, break
                    break
            # Save the received data to the specified file
            with open(self.args.upload, "wb") as f:
                f.write(file_buffer)
            # Send confirmation message to client
            message = f"Saved file {self.args.upload}"
            client_socket.send(message.encode())
            
        elif self.args.command:  # If -c flag is set, start an interactive shell
            cmd_buffer = b""  # Buffer for command input
            while True:
                try:
                    # Send a prompt to the client
                    client_socket.send(b"BHP: #> ")
                    # Receive command until newline is found
                    while "\n" not in cmd_buffer.decode():
                        cmd_buffer += client_socket.recv(64)
                    # Execute the received command
                    response = execute(cmd_buffer.decode())
                    if response:  # If there's output, send it to client
                        client_socket.send(response.encode())
                    cmd_buffer = b""  # Reset buffer for next command
                except Exception as e:  # Handle errors (e.g., client disconnect)
                    print(f"Server killed: {e}")
                    client_socket.close()
                    self.socket.close()
                    sys.exit()
        
        client_socket.close()  # Close client socket when done

# Main block to set up command-line arguments and start the program
if __name__ == "__main__":
    # Create argument parser with a description and example usage
    parser = argparse.ArgumentParser(
        description="A simple network communication tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""Examples:
            netcat.py -t 192.168.1.108 -p 5555 -l -c  # Start a command shell
            netcat.py -t 192.168.1.108 -p 5555 -l -u=mytest.txt  # Upload a file
            netcat.py -t 192.168.1.108 -p 5555 -l -e="cat /etc/passwd"  # Execute a command
            echo 'ABC' | ./netcat.py -t 192.168.1.108 -p 135  # Send text to a port
            netcat.py -t 192.168.1.108 -p 5555  # Connect to a server
        """)
    )
    
    # Add command-line arguments
    parser.add_argument("-c", "--command", action="store_true", help="Start an interactive command shell")
    parser.add_argument("-e", "--execute", help="Execute a specific command")
    parser.add_argument("-l", "--listen", action="store_true", help="Listen for incoming connections")
    parser.add_argument("-p", "--port", type=int, default=5555, help="Port to connect or listen on")
    parser.add_argument("-t", "--target", default="192.168.1.203", help="Target IP address")
    parser.add_argument("-u", "--upload", help="File to save uploaded data to")
    
    # Parse the arguments
    args = parser.parse_args()
    
    # If listening, use an empty buffer; otherwise, read from stdin
    if args.listen:
        buffer = ""
    else:
        buffer = sys.stdin.read()
    
    # Create NetCat object and start it
    nc = NetCat(args, buffer.encode())
    nc.run()