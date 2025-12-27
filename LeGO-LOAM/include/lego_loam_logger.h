#ifndef _LEGO_LOAM_LOGGER_H_
#define _LEGO_LOAM_LOGGER_H_

#include <fstream>
#include <sstream>
#include <iostream>
#include <string>
#include <mutex>
#include <ctime>
#include <iomanip>
#include <chrono>

// Singleton logger class to avoid multiple definition issues
class LeGOLOAMLogger {
private:
    std::mutex log_mutex_;
    std::string log_dir_;
    std::ofstream log_file_;
    bool initialized_;
    bool enable_console_output_;
    bool enable_file_output_;

    // Private constructor for singleton
    LeGOLOAMLogger() 
        : log_dir_("/tmp/lego_loam_logs/")
        , initialized_(false)
        , enable_console_output_(true)
        , enable_file_output_(true) {}

    // Get timestamp in format: YYYY-MM-DD HH:MM:SS.mmm
    std::string getTimestamp() {
        auto now = std::time(nullptr);
        auto tm = *std::localtime(&now);
        std::ostringstream oss;
        oss << std::put_time(&tm, "%Y-%m-%d %H:%M:%S");
        return oss.str();
    }

    // Get current time in milliseconds
    std::string getMilliseconds() {
        auto now = std::chrono::system_clock::now();
        auto ms = std::chrono::duration_cast<std::chrono::milliseconds>(
            now.time_since_epoch()) % 1000;
        std::ostringstream oss;
        oss << std::setfill('0') << std::setw(3) << ms.count();
        return oss.str();
    }

    // Get singleton instance
    static LeGOLOAMLogger& getInstance() {
        static LeGOLOAMLogger instance;
        return instance;
    }

    void initImpl(const std::string& log_directory) {
        std::lock_guard<std::mutex> lock(log_mutex_);
        
        if (initialized_) return;
        
        log_dir_ = log_directory;
        
        // Create directory if it doesn't exist
        system(("mkdir -p " + log_dir_).c_str());
        
        // Open main log file
        std::string log_file_path = log_dir_ + "lego_loam_debug.log";
        log_file_.open(log_file_path, std::ios::app);
        
        initialized_ = true;
    }

    void logImpl(int level, const std::string& node_name, 
                 const std::string& message) {
        if (!initialized_) {
            initImpl("/tmp/lego_loam_logs/");
        }

        std::lock_guard<std::mutex> lock(log_mutex_);
        
        std::string timestamp = getTimestamp() + "." + getMilliseconds();
        std::string level_str;
        
        switch (level) {
            case 0:  level_str = "DEBUG"; break;
            case 1:  level_str = "INFO "; break;
            case 2:  level_str = "WARN "; break;
            case 3:  level_str = "ERROR"; break;
            default: level_str = "???? "; break;
        }
        
        std::string formatted_msg = "[" + timestamp + "] [" + level_str + "] [" 
                                   + node_name + "] " + message;
        
        // Write to file
        if (enable_file_output_ && log_file_.is_open()) {
            log_file_ << formatted_msg << std::endl;
            log_file_.flush();
        }
        
        // Also output to console for real-time monitoring
        if (enable_console_output_) {
            std::cout << formatted_msg << std::endl;
        }
    }

public:
    enum LogLevel {
        DEBUG = 0,
        INFO = 1,
        WARNING = 2,
        ERROR = 3
    };

    // Prevent copying
    LeGOLOAMLogger(const LeGOLOAMLogger&) = delete;
    LeGOLOAMLogger& operator=(const LeGOLOAMLogger&) = delete;

    // Static interface functions
    static void init(const std::string& log_directory = "/tmp/lego_loam_logs/") {
        getInstance().initImpl(log_directory);
    }

    static void log(LogLevel level, const std::string& node_name, 
                    const std::string& message) {
        getInstance().logImpl(static_cast<int>(level), node_name, message);
    }

    static void setConsoleOutput(bool enable) {
        getInstance().enable_console_output_ = enable;
    }

    static void setFileOutput(bool enable) {
        getInstance().enable_file_output_ = enable;
    }

    static void shutdown() {
        auto& inst = getInstance();
        std::lock_guard<std::mutex> lock(inst.log_mutex_);
        if (inst.log_file_.is_open()) {
            inst.log_file_.close();
        }
    }

    static std::string getLogDirectory() {
        return getInstance().log_dir_;
    }
};

#endif // _LEGO_LOAM_LOGGER_H_
