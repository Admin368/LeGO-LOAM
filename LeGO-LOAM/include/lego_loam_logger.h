#ifndef _LEGO_LOAM_LOGGER_H_
#define _LEGO_LOAM_LOGGER_H_

#include <fstream>
#include <sstream>
#include <iostream>
#include <string>
#include <mutex>
#include <ctime>
#include <iomanip>
#include <ros/ros.h>

class LeGOLOAMLogger {
private:
    static std::mutex log_mutex_;
    static std::string log_dir_;
    static std::ofstream log_file_;
    static bool initialized_;
    static bool enable_console_output_;
    static bool enable_file_output_;

    // Get timestamp in format: YYYY-MM-DD HH:MM:SS.mmm
    static std::string getTimestamp() {
        auto now = std::time(nullptr);
        auto tm = *std::localtime(&now);
        std::ostringstream oss;
        oss << std::put_time(&tm, "%Y-%m-%d %H:%M:%S");
        return oss.str();
    }

    // Get current time in milliseconds (appended to timestamp)
    static std::string getMilliseconds() {
        auto now = std::chrono::system_clock::now();
        auto ms = std::chrono::duration_cast<std::chrono::milliseconds>(
            now.time_since_epoch()) % 1000;
        std::ostringstream oss;
        oss << std::setfill('0') << std::setw(3) << ms.count();
        return oss.str();
    }

public:
    enum LogLevel {
        DEBUG,
        INFO,
        WARNING,
        ERROR
    };

    // Initialize logger with directory path
    static void init(const std::string& log_directory = "/tmp/lego_loam_logs/") {
        std::lock_guard<std::mutex> lock(log_mutex_);
        
        if (initialized_) return;
        
        log_dir_ = log_directory;
        
        // Create directory if it doesn't exist
        system(("mkdir -p " + log_dir_).c_str());
        
        // Open main log file
        std::string log_file_path = log_dir_ + "lego_loam_debug.log";
        log_file_.open(log_file_path, std::ios::app);
        
        initialized_ = true;
        enable_console_output_ = true;
        enable_file_output_ = true;
    }

    // Log message with level and node name
    static void log(LogLevel level, const std::string& node_name, 
                    const std::string& message) {
        if (!initialized_) {
            init();
        }

        std::lock_guard<std::mutex> lock(log_mutex_);
        
        std::string timestamp = getTimestamp() + "." + getMilliseconds();
        std::string level_str;
        
        switch (level) {
            case DEBUG:   level_str = "DEBUG"; break;
            case INFO:    level_str = "INFO "; break;
            case WARNING: level_str = "WARN "; break;
            case ERROR:   level_str = "ERROR"; break;
            default:      level_str = "???? "; break;
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

    // Convenience functions for each node
    static void logImageProjection(const std::string& message) {
        log(DEBUG, "ImageProjection", message);
    }

    static void logFeatureAssociation(const std::string& message) {
        log(DEBUG, "FeatureAssociation", message);
    }

    static void logMapOptimization(const std::string& message) {
        log(DEBUG, "MapOptimization", message);
    }

    static void logTransformFusion(const std::string& message) {
        log(DEBUG, "TransformFusion", message);
    }

    // Enable/disable output
    static void setConsoleOutput(bool enable) {
        console_output_ = enable;
    }

    static void setFileOutput(bool enable) {
        file_output_ = enable;
    }

    // Close logger
    static void shutdown() {
        std::lock_guard<std::mutex> lock(log_mutex_);
        if (log_file_.is_open()) {
            log_file_.close();
        }
    }

    // Get log directory
    static std::string getLogDirectory() {
        return log_dir_;
    }
};

// Static member initialization
std::mutex LeGOLOAMLogger::log_mutex_;
std::string LeGOLOAMLogger::log_dir_ = "/tmp/lego_loam_logs/";
std::ofstream LeGOLOAMLogger::log_file_;
bool LeGOLOAMLogger::initialized_ = false;
bool LeGOLOAMLogger::enable_console_output_ = true;
bool LeGOLOAMLogger::enable_file_output_ = true;

#endif // _LEGO_LOAM_LOGGER_H_
