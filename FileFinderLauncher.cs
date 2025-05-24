using System;
using System.Diagnostics;
using System.IO;
using System.Windows.Forms;

class Program
{
    [STAThread]
    static void Main()
    {
        string[] pythonCmds = { "python", "python3" };
        string pythonInstaller = "python-installer.exe"; // Place a Python installer in the same folder

        bool pythonFound = false;
        foreach (var pythonCmd in pythonCmds)
        {
            try
            {
                ProcessStartInfo psi = new ProcessStartInfo
                {
                    FileName = pythonCmd,
                    Arguments = "--version",
                    RedirectStandardOutput = true,
                    UseShellExecute = false,
                    CreateNoWindow = true
                };
                using (Process proc = Process.Start(psi))
                {
                    proc.WaitForExit(2000);
                    if (proc.ExitCode == 0)
                    {
                        pythonFound = true;
                        break;
                    }
                }
            }
            catch { }
        }

        if (pythonFound)
        {
            MessageBox.Show("Python is already installed on this system.", "Python Found", MessageBoxButtons.OK, MessageBoxIcon.Information);
            return;
        }

        // Python not found, run installer
        if (File.Exists(pythonInstaller))
        {
            MessageBox.Show("Python not found. The installer will now run.", "Installing Python", MessageBoxButtons.OK, MessageBoxIcon.Information);
            Process.Start(pythonInstaller);
        }
        else
        {
            MessageBox.Show("Python is not installed and the installer was not found in this folder.", "Installer Not Found", MessageBoxButtons.OK, MessageBoxIcon.Error);
        }
    }
}
