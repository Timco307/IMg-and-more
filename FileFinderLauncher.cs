using System;
using System.Diagnostics;
using System.IO;
using System.Windows.Forms;

class Program
{
    [STAThread]
    static void Main()
    {
        string pythonCmd = "python";
        string script = "file_finder_gui.py";
        string pythonInstaller = "python-installer.exe"; // Place a Python installer in the same folder if desired
        string pythonUrl = "https://www.python.org/downloads/";

        // Try to run "python --version"
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
                    // Python found, run the script
                    Process.Start(pythonCmd, script);
                    return;
                }
            }
        }
        catch { }

        // Python not found
        DialogResult result = MessageBox.Show(
            "Python is not installed. Would you like to install it now?",
            "Python Not Found",
            MessageBoxButtons.YesNo,
            MessageBoxIcon.Warning);

        if (result == DialogResult.Yes)
        {
            if (File.Exists(pythonInstaller))
            {
                Process.Start(pythonInstaller);
            }
            else
            {
                Process.Start(new ProcessStartInfo
                {
                    FileName = pythonUrl,
                    UseShellExecute = true
                });
            }
        }
    }
}
