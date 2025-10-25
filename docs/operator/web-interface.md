# 🌐 Web Interface Guide

Retrovue's modern web interface makes setup and management much easier than using the command line. This guide covers all the features and workflows available in the web UI.

## 🚀 Getting Started

### **Launch the Web Interface**

```powershell
# Windows
uvicorn retrovue.api.main:app --app-dir src --host 127.0.0.1 --port 8000 --reload

# macOS/Linux
uvicorn retrovue.api.main:app --app-dir src --host 127.0.0.1 --port 8000 --reload
```

Then open your browser to: **http://localhost:8000**

## 📋 Interface Overview

The web interface is organized into several main tabs:

- **Servers** - Manage Plex server connections
- **Libraries** - Discover and configure Plex libraries
- **Content Sync** - Import content with real-time progress
- **Content Browser** - View and manage imported content
- **Streaming** - Control streaming operations (coming soon)

## 🖥️ Servers Tab

### **Add a Plex Server**

1. **Click the "Servers" tab**
2. **Enter server details**:
   - **Name**: Friendly name (e.g., "Home Plex")
   - **URL**: `http://your-plex-server:32400`
   - **Token**: [How to get your token](https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/)
3. **Click "Add Server"**

### **Get Your Plex Token**

1. Open Plex Web Interface: `http://your-plex-server:32400/web`
2. Press `F12` → Network tab → Refresh page
3. Find `X-Plex-Token` in request headers
4. Copy the token value

### **Server Management**

- **View all servers**: See all configured Plex servers
- **Test connection**: Verify server connectivity
- **Edit settings**: Update server configuration
- **Remove server**: Delete server configuration

## 📚 Libraries Tab

### **Discover Libraries**

1. **Click the "Libraries" tab**
2. **Select your server** from the dropdown
3. **Click "Discover Libraries"** button
4. **Review discovered libraries**:
   - Library name and type
   - Content count
   - Last updated timestamp
5. **Check the boxes** for libraries you want to sync
6. **Changes are saved automatically**

### **Library Configuration**

- **Enable/Disable**: Toggle library synchronization
- **View Details**: See library metadata and content counts
- **Sync Status**: Track synchronization progress
- **Error Handling**: View and resolve sync errors

## 🔄 Content Sync Tab

### **Configure Path Mappings**

Path mappings are **critical** for streaming to work properly. They translate Plex's internal paths to accessible local file paths.

#### **Add Path Mapping**

1. **Click the "Content Sync" tab**
2. **Select server and library** from dropdowns
3. **Add path mapping**:
   - **Plex Path**: Path as seen by Plex (e.g., `/mnt/media/movies`)
   - **Local Path**: Corresponding path on your machine (e.g., `D:\Movies`)
   - **Click "Add Mapping"**

#### **Example Path Mappings**

```bash
# Windows example
Plex Path: /mnt/media/movies
Local Path: D:\Media\Movies

# Linux example
Plex Path: /data/movies
Local Path: /home/user/media/movies

# macOS example
Plex Path: /Volumes/Media/Movies
Local Path: /Users/username/Movies
```

### **Sync Content**

#### **Preview Content (Dry Run)**

1. **Set sync limit** (optional, useful for testing)
2. **Click "Dry Run (Preview)"** to test without making changes
3. **Review the preview** in the log viewer
4. **Check for errors** and resolve any issues

#### **Import Content**

1. **Click "Sync (Write to DB)"** to import content
2. **Watch real-time progress** in the log viewer
3. **Monitor sync status** and completion
4. **Review any errors** that occur during sync

### **Real-Time Progress**

The web interface provides real-time feedback during sync operations:

- **Progress indicators** show current operation status
- **Log viewer** displays detailed sync information
- **Error highlighting** makes issues easy to identify
- **Non-blocking UI** keeps the interface responsive

## 📁 Content Browser Tab

### **View Imported Content**

The Content Browser shows all imported content with rich metadata:

- **Content type** (movies, TV shows, episodes)
- **Title and metadata** from Plex
- **File information** (size, duration, codecs)
- **Sync status** and last updated timestamp
- **Path resolution** status

### **Content Management**

- **Search and filter** content by various criteria
- **View detailed metadata** for each item
- **Check file accessibility** and validation status
- **Manage content states** (Normal, RemoteOnly, Unavailable)

## 🎛️ Streaming Tab (Coming Soon)

### **Channel Management**

- **Start/Stop channels** with simple controls
- **Monitor stream status** and performance
- **View active streams** and their details
- **Emergency controls** for immediate actions

### **Stream Configuration**

- **Quality settings** for different devices
- **Channel lineup** management
- **Schedule preview** and timeline view
- **Performance monitoring** and alerts

## 🔧 Advanced Features

### **Real-Time Updates**

The web interface provides real-time updates for all operations:

- **Live progress tracking** during long operations
- **Automatic refresh** of status information
- **Error notifications** with detailed information
- **Success confirmations** for completed operations

### **Error Handling**

- **Comprehensive error reporting** with detailed messages
- **Error categorization** for easier troubleshooting
- **Recovery suggestions** for common issues
- **Log export** for technical support

### **Performance Monitoring**

- **Sync performance metrics** and timing
- **Resource usage** monitoring
- **Error rate tracking** and analysis
- **System health** indicators

## 🛠️ Troubleshooting

### **Common Issues**

#### **Server Connection Failed**

- Check Plex server URL (include http:// and port)
- Verify Plex token is correct
- Ensure Plex server is running and accessible
- Check firewall settings

#### **Path Mapping Issues**

- Verify local paths exist and are accessible
- Check path format (use forward slashes on Windows)
- Ensure sufficient disk space
- Verify file permissions

#### **Sync Errors**

- Check network connectivity to Plex server
- Verify Plex server has sufficient resources
- Review error messages in the log viewer
- Try reducing sync limit for testing

#### **UI Not Responding**

- Refresh the browser page
- Check browser console for JavaScript errors
- Verify Python server is still running
- Restart the web interface if needed

### **Getting Help**

- **Error Messages**: All errors are displayed with detailed information
- **Log Viewer**: Real-time logs help diagnose issues
- **Tooltips**: Hover over buttons for helpful guidance
- **Documentation**: Check other guides for detailed information

## 🎯 Best Practices

### **Initial Setup**

1. **Start with one server** and one library for testing
2. **Use dry run mode** to verify configuration before importing
3. **Set small sync limits** initially to test the process
4. **Verify path mappings** work correctly before full sync

### **Production Use**

1. **Monitor sync performance** and adjust limits as needed
2. **Regular maintenance** of path mappings and server connections
3. **Error monitoring** and proactive issue resolution
4. **Backup configuration** and database regularly

### **Performance Optimization**

1. **Batch operations** when possible for better performance
2. **Monitor resource usage** during large sync operations
3. **Schedule syncs** during off-peak hours
4. **Use appropriate sync limits** for your system

## 🎉 Next Steps

After successfully setting up your content:

1. **Explore the Content Browser** to see your imported media
2. **Check the [Streaming Guide](streaming.md)** for streaming setup
3. **Review [Configuration Guide](configuration.md)** for advanced settings
4. **Read [Troubleshooting Guide](troubleshooting.md)** for common issues

---

The web interface makes Retrovue much more accessible and user-friendly. Enjoy your retro IPTV system! 📺✨
