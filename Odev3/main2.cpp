#include <windows.h>
#include <iostream>
#include <fstream>
#include <string>
#include <vector>
#include <filesystem>
#include <future>
#include <commctrl.h>
#include <shlobj.h> 

namespace fs = std::filesystem;

// --- ANALİZ MOTORU ---
class HardeningChecker {
private:
    std::string filePath;
    std::vector<std::string> suspiciousAPIs = {
        "ShellExecute", "System", "CreateProcess", "WriteProcessMemory", 
        "CreateRemoteThread", "WinExec", "HttpOpenRequest", "InternetOpen"
    };
    std::vector<std::string> knownMalwareHashes = {
        "d41d8cd98f00b204e9800998ecf8427e", "098f6bcd4621d373cade4e832627b4f6"
    };

public:
    HardeningChecker(std::string path) : filePath(path) {}

    int calculateRiskScore(int threatCount, int hardeningMissing) {
        int score = (hardeningMissing * 15) + (threatCount * 20);
        return (score > 100) ? 100 : score;
    }

    void runAnalysis(HWND hList) {
        std::ifstream file(filePath, std::ios::binary);
        if (!file) return;

        // PE Header Okuma
        int32_t peHeaderOffset = 0;
        file.seekg(0x3C);
        file.read(reinterpret_cast<char*>(&peHeaderOffset), 4);

        uint16_t dllChar = 0;
        file.seekg(peHeaderOffset + 24 + 70); 
        file.read(reinterpret_cast<char*>(&dllChar), 2);

        // API Taraması
        std::ifstream sFile(filePath, std::ios::binary);
        std::string content((std::istreambuf_iterator<char>(sFile)), std::istreambuf_iterator<char>());
        
        int threatCount = 0;
        for (const auto& api : suspiciousAPIs) {
            if (content.find(api) != std::string::npos) threatCount++;
        }

        int missing = 0;
        if (!(dllChar & 0x0040)) missing++;
        if (!(dllChar & 0x0100)) missing++;

        int score = calculateRiskScore(threatCount, missing);

        // SONUCU ARAYÜZE (LISTBOX) YAZDIR
        std::string result = "[" + std::to_string(score) + "%] " + fs::path(filePath).filename().string();
        if(score > 50) result += " -> KRITIK!";
        else result += " -> Guvenli";

        SendMessage(hList, LB_ADDSTRING, 0, (LPARAM)result.c_str());
    }
};

// --- ARAYÜZ YÖNETİMİ ---
HWND hList;

LRESULT CALLBACK WindowProcedure(HWND hwnd, UINT msg, WPARAM wParam, LPARAM lParam) {
    switch (msg) {
       	case WM_CTLCOLORSTATIC:
{
    HDC hdcStatic = (HDC)wParam;
    SetTextColor(hdcStatic, RGB(0, 255, 255)); // Yazıları Turkuaz yap
    SetBkColor(hdcStatic, RGB(30, 30, 30));    // Arka planı koyulaştır
    return (INT_PTR)CreateSolidBrush(RGB(30, 30, 30));
}
case WM_CTLCOLORLISTBOX:
{
    HDC hdcList = (HDC)wParam;
    SetTextColor(hdcList, RGB(0, 255, 0)); // Liste yazılarını Yeşil yap
    SetBkColor(hdcList, RGB(20, 20, 20));
    return (INT_PTR)CreateSolidBrush(RGB(20, 20, 20));
}
        case WM_CREATE:
            // Buton
            CreateWindow("BUTTON", "TARAMAYI BASLAT", WS_VISIBLE | WS_CHILD | BS_FLAT, 
                         20, 20, 150, 40, hwnd, (HMENU)1, NULL, NULL);
            // Sonuç Listesi
            hList = CreateWindow("LISTBOX", NULL, WS_VISIBLE | WS_CHILD | LBS_NOTIFY | WS_VSCROLL | WS_BORDER, 
                                 20, 80, 440, 250, hwnd, NULL, NULL, NULL);
            break;

        case WM_COMMAND: {
            if (LOWORD(wParam) == 1) { // Butona basıldığında
                char szDir[MAX_PATH];
                BROWSEINFO bi = { 0 };
                bi.lpszTitle = "Analiz Edilecek Klasörü Seçin";
                bi.ulFlags = BIF_RETURNONLYFSDIRS | BIF_NEWDIALOGSTYLE; // Modern görünüm
                
                LPITEMIDLIST pidl = SHBrowseForFolder(&bi);

                if (pidl != 0) {
                    // Seçilen klasörün yolunu al
                    SHGetPathFromIDList(pidl, szDir);
                    std::string folder = szDir;
                    
                    // Listeyi temizle ve taramaya başla
                    SendMessage(hList, LB_RESETCONTENT, 0, 0);
                    
                    try {
                        for (const auto& entry : fs::directory_iterator(folder)) {
                            if (entry.path().extension() == ".exe") {
                                HardeningChecker checker(entry.path().string());
                                checker.runAnalysis(hList);
                            }
                        }
                        MessageBox(hwnd, "Tarama tamamlandi", "Velox Security", MB_OK | MB_ICONINFORMATION);
                    } catch (const std::exception& e) {
    // e.what() hatanın tam teknik sebebini (İngilizce olarak) söyler
    std::string fullError = "Sistem Hatası: " + std::string(e.what());
    MessageBox(hwnd, fullError.c_str(), "Velox Security", MB_OK | MB_ICONERROR);

                    }
                }
            }
            break;
        }

        case WM_DESTROY:
            PostQuitMessage(0);
            break;

        default:
            return DefWindowProc(hwnd, msg, wParam, lParam);
    }
    return 0;
}

int WINAPI WinMain(HINSTANCE hInst, HINSTANCE hPrev, LPSTR args, int nShow) {
    WNDCLASS wc = {0};
    wc.hbrBackground = (HBRUSH)COLOR_WINDOW;
    wc.hCursor = LoadCursor(NULL, IDC_ARROW);
    wc.hInstance = hInst;
    wc.lpszClassName = "VeloxGUI";
    wc.lpfnWndProc = WindowProcedure;

    if (!RegisterClass(&wc)) return -1;

    CreateWindow("VeloxGUI", "Velox Security Suite v1.0", WS_OVERLAPPEDWINDOW | WS_VISIBLE, 
                 100, 100, 500, 400, NULL, NULL, NULL, NULL);

    MSG msg = {0};
    while (GetMessage(&msg, NULL, 0, 0)) {
        TranslateMessage(&msg);
        DispatchMessage(&msg);
    }
    return 0;
}