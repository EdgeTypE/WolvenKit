// @version 1.0
// @author WolvenKit
// @type general
// @description
// Export Cyberpunk 2077 NPC Character with Selected Appearance
// 
// This script exports a specified NPC character (e.g., Songbird) with the selected
// appearance to GLB format (FBX-compatible) along with textures as PNG files.
// 
// The script will:
// 1. Find the character's entity file (.ent) in game archives
// 2. List available appearances
// 3. Export the selected appearance's meshes and textures
// 4. Convert textures to PNG format
//
// @usage
// 1. Open a WolvenKit project
// 2. Configure the NPC name and appearance name in the settings dialog
// 3. Run the script
// 4. Files will be extracted to your project and exported to the Raw folder

// Configuration with settings dialog
var settings = {
    npcName: {
        type: "string",
        label: "NPC Name",
        description: "The name of the NPC character to export (e.g., songbird, johnny, panam, judy, rogue, kerry, v)",
        value: "songbird"
    },
    appearanceName: {
        type: "string", 
        label: "Appearance Name",
        description: "The appearance name to export (e.g., default, casual, combat). Use 'default' for the first appearance.",
        value: "default"
    },
    exportTextures: {
        type: "bool",
        label: "Export Textures",
        description: "If enabled, textures will be exported as PNG files",
        value: true
    }
};

// Show settings dialog
if (!wkit.ShowSettings(settings)) {
    logger.Info("Export cancelled by user");
} else {
    try {
        exportNpcWithAppearance(settings.npcName.value, settings.appearanceName.value, settings.exportTextures.value);
    } catch (ex) {
        logger.Error("Export failed: " + (ex.message || ex));
        logger.Info("Please check the log for details and ensure a project is open");
    }
}

function exportNpcWithAppearance(npcName, appearanceName, exportTextures) {
    logger.Info("=== NPC Character Export Script ===");
    logger.Info("NPC Name: " + npcName);
    logger.Info("Appearance: " + appearanceName);
    
    // Common NPC entity paths in Cyberpunk 2077
    var entityPaths = findNpcEntityPaths(npcName);
    
    if (entityPaths.length === 0) {
        logger.Error("No entity files found for NPC: " + npcName);
        logger.Info("Try searching the Asset Browser for the character name");
        return;
    }
    
    logger.Info("Found " + entityPaths.length + " potential entity file(s)");
    
    var processedFiles = [];
    var meshFiles = [];
    var textureFiles = [];
    
    // Process each entity file found
    for (var i = 0; i < entityPaths.length; i++) {
        var entityPath = entityPaths[i];
        logger.Info("Processing entity: " + entityPath);
        
        try {
            // Extract the entity file to project
            wkit.Extract(entityPath);
            processedFiles.push(entityPath);
            
            // Get the entity file as CR2W to analyze its structure
            var entityFile = wkit.GetFileFromArchive(entityPath, OpenAs.CR2W);
            if (!entityFile) {
                logger.Warning("Could not load entity file: " + entityPath);
                continue;
            }
            
            // Find appearances and mesh components
            var result = analyzeEntity(entityFile, appearanceName);
            
            if (result.meshPaths.length > 0) {
                for (var m = 0; m < result.meshPaths.length; m++) {
                    var meshPath = result.meshPaths[m];
                    if (meshPath && meshFiles.indexOf(meshPath) === -1) {
                        meshFiles.push(meshPath);
                    }
                }
            }
            
            if (result.texturePaths.length > 0) {
                for (var t = 0; t < result.texturePaths.length; t++) {
                    var texPath = result.texturePaths[t];
                    if (texPath && textureFiles.indexOf(texPath) === -1) {
                        textureFiles.push(texPath);
                    }
                }
            }
            
            // Process appearance files
            for (var a = 0; a < result.appearanceFiles.length; a++) {
                var appPath = result.appearanceFiles[a];
                if (appPath) {
                    logger.Info("Extracting appearance file: " + appPath);
                    wkit.Extract(appPath);
                    processedFiles.push(appPath);
                    
                    // Analyze appearance file for meshes
                    var appFile = wkit.GetFileFromArchive(appPath, OpenAs.CR2W);
                    if (appFile) {
                        var appResult = analyzeAppearance(appFile, appearanceName);
                        for (var am = 0; am < appResult.meshPaths.length; am++) {
                            if (meshFiles.indexOf(appResult.meshPaths[am]) === -1) {
                                meshFiles.push(appResult.meshPaths[am]);
                            }
                        }
                        for (var at = 0; at < appResult.texturePaths.length; at++) {
                            if (textureFiles.indexOf(appResult.texturePaths[at]) === -1) {
                                textureFiles.push(appResult.texturePaths[at]);
                            }
                        }
                    }
                }
            }
        } catch (ex) {
            logger.Error("Error processing entity " + entityPath + ": " + ex.message);
        }
    }
    
    // Extract mesh files
    logger.Info("Found " + meshFiles.length + " mesh file(s) to extract");
    for (var mi = 0; mi < meshFiles.length; mi++) {
        try {
            logger.Info("Extracting mesh: " + meshFiles[mi]);
            wkit.Extract(meshFiles[mi]);
            processedFiles.push(meshFiles[mi]);
        } catch (ex) {
            logger.Warning("Could not extract mesh: " + meshFiles[mi]);
        }
    }
    
    // Extract and export texture files
    if (exportTextures) {
        logger.Info("Found " + textureFiles.length + " texture file(s) to extract");
        for (var ti = 0; ti < textureFiles.length; ti++) {
            try {
                logger.Info("Extracting texture: " + textureFiles[ti]);
                wkit.Extract(textureFiles[ti]);
                processedFiles.push(textureFiles[ti]);
            } catch (ex) {
                logger.Warning("Could not extract texture: " + textureFiles[ti]);
            }
        }
    }
    
    // Export meshes to GLB format (FBX-compatible, widely supported)
    if (meshFiles.length > 0) {
        logger.Info("Exporting meshes to GLB format...");
        
        var meshExportSettings = {
            Mesh: {
                MeshExporter: "Default",
                ExportType: "MeshOnly",
                LodFilter: true,
                Binary: true,
                WithMaterials: exportTextures,
                ImageType: "png"
            }
        };
        
        var exportList = [];
        for (var ei = 0; ei < meshFiles.length; ei++) {
            exportList.push(meshFiles[ei]);
        }
        
        try {
            wkit.ExportFiles(exportList, meshExportSettings);
            logger.Info("Mesh export completed!");
        } catch (ex) {
            logger.Error("Error exporting meshes: " + ex.message);
        }
    }
    
    // Export texture files to PNG
    if (exportTextures && textureFiles.length > 0) {
        logger.Info("Exporting textures to PNG format...");
        
        var textureExportSettings = {
            Xbm: {
                ImageType: "png"
            }
        };
        
        var textureExportList = [];
        for (var tei = 0; tei < textureFiles.length; tei++) {
            textureExportList.push(textureFiles[tei]);
        }
        
        try {
            wkit.ExportFiles(textureExportList, textureExportSettings);
            logger.Info("Texture export completed!");
        } catch (ex) {
            logger.Error("Error exporting textures: " + ex.message);
        }
    }
    
    // Summary
    logger.Info("=== Export Summary ===");
    logger.Info("Total files processed: " + processedFiles.length);
    logger.Info("Meshes exported: " + meshFiles.length);
    logger.Info("Textures exported: " + textureFiles.length);
    logger.Info("Files are in your project's archive folder");
    logger.Info("Exported GLB files are in your project's raw folder");
    logger.Info("Note: GLB format is compatible with Blender and most 3D software. Use Blender to convert to FBX if needed.");
}

function findNpcEntityPaths(npcName) {
    var paths = [];
    var searchName = npcName.toLowerCase();
    
    // Common paths for NPC entities in Cyberpunk 2077
    var searchPatterns = [
        "base\\characters\\entities\\main_npc\\",
        "base\\characters\\entities\\gang\\",
        "base\\characters\\entities\\citizen\\",
        "base\\characters\\entities\\corpo\\",
        "base\\characters\\entities\\player\\",
        "ep1\\characters\\entities\\"
    ];
    
    // Known NPC mappings for common characters
    var knownNpcs = {
        "songbird": [
            "base\\characters\\entities\\main_npc\\songbird.ent",
            "ep1\\characters\\entities\\main_npc\\songbird.ent"
        ],
        "johnny": [
            "base\\characters\\entities\\main_npc\\johnny.ent",
            "base\\characters\\entities\\main_npc\\johnny_intros.ent"
        ],
        "panam": [
            "base\\characters\\entities\\main_npc\\panam.ent"
        ],
        "judy": [
            "base\\characters\\entities\\main_npc\\judy.ent"
        ],
        "rogue": [
            "base\\characters\\entities\\main_npc\\rogue.ent"
        ],
        "kerry": [
            "base\\characters\\entities\\main_npc\\kerry.ent"
        ],
        "v": [
            "base\\characters\\entities\\player\\main_player.ent"
        ],
        "jackie": [
            "base\\characters\\entities\\main_npc\\jackie.ent"
        ],
        "evelyn": [
            "base\\characters\\entities\\main_npc\\evelyn.ent"
        ],
        "takemura": [
            "base\\characters\\entities\\main_npc\\takemura.ent"
        ],
        "dexter": [
            "base\\characters\\entities\\main_npc\\dexter.ent"
        ],
        "adam_smasher": [
            "base\\characters\\entities\\main_npc\\adam_smasher.ent"
        ],
        "hanako": [
            "base\\characters\\entities\\main_npc\\hanako.ent"
        ],
        "yorinobu": [
            "base\\characters\\entities\\main_npc\\yorinobu.ent"
        ],
        "saburo": [
            "base\\characters\\entities\\main_npc\\saburo.ent"
        ],
        "reed": [
            "ep1\\characters\\entities\\main_npc\\reed.ent"
        ],
        "myers": [
            "ep1\\characters\\entities\\main_npc\\president_myers.ent"
        ],
        "alex": [
            "ep1\\characters\\entities\\main_npc\\alex.ent"
        ]
    };
    
    // Check known NPC mappings first
    if (knownNpcs[searchName]) {
        var knownPaths = knownNpcs[searchName];
        for (var k = 0; k < knownPaths.length; k++) {
            if (wkit.FileExistsInArchive(knownPaths[k])) {
                paths.push(knownPaths[k]);
            }
        }
    }
    
    // If no known paths found, search through archive files
    if (paths.length === 0) {
        logger.Info("Searching archives for NPC: " + searchName);
        
        var archiveFiles = wkit.GetArchiveFiles();
        var count = 0;
        // Limit search results to prevent performance issues when iterating through thousands of archive files
        var MAX_SEARCH_RESULTS = 10;
        
        // Use iterator pattern for IEnumerable from .NET
        var enumerator = archiveFiles.GetEnumerator();
        try {
            while (enumerator.MoveNext()) {
                var file = enumerator.Current;
                if (file && file.FileName) {
                    var fileName = file.FileName.toLowerCase();
                    if (fileName.indexOf(searchName) !== -1 && fileName.endsWith(".ent")) {
                        paths.push(file.FileName);
                        count++;
                        if (count >= MAX_SEARCH_RESULTS) {
                            break;
                        }
                    }
                }
            }
        } catch (iterEx) {
            logger.Warning("Error iterating archive files: " + (iterEx.message || iterEx));
        }
    }
    
    return paths;
}

function analyzeEntity(entityFile, targetAppearance) {
    var result = {
        meshPaths: [],
        texturePaths: [],
        appearanceFiles: [],
        rigPaths: []
    };
    
    try {
        var root = entityFile.RootChunk;
        if (!root) return result;
        
        // Check for entity template structure
        if (root.Appearances) {
            for (var i = 0; i < root.Appearances.length; i++) {
                var app = root.Appearances[i];
                if (app && app.AppearanceResource && app.AppearanceResource.DepotPath) {
                    var appPath = app.AppearanceResource.DepotPath.toString();
                    if (appPath && appPath.length > 0 && result.appearanceFiles.indexOf(appPath) === -1) {
                        result.appearanceFiles.push(appPath);
                    }
                }
            }
        }
        
        // Check for compiled data
        if (root.CompiledData && root.CompiledData.Data && root.CompiledData.Data.Chunks) {
            var chunks = root.CompiledData.Data.Chunks;
            for (var c = 0; c < chunks.length; c++) {
                var chunk = chunks[c];
                extractPathsFromChunk(chunk, result);
            }
        }
        
        // Check for components array directly
        if (root.Components) {
            for (var comp = 0; comp < root.Components.length; comp++) {
                var component = root.Components[comp];
                extractPathsFromChunk(component, result);
            }
        }
    } catch (ex) {
        logger.Warning("Error analyzing entity: " + ex.message);
    }
    
    return result;
}

function analyzeAppearance(appFile, targetAppearance) {
    var result = {
        meshPaths: [],
        texturePaths: []
    };
    
    try {
        var root = appFile.RootChunk;
        if (!root) return result;
        
        // Check for appearances array
        if (root.Appearances) {
            for (var i = 0; i < root.Appearances.length; i++) {
                var app = root.Appearances[i];
                if (!app) continue;
                
                var appDef = app.GetValue ? app.GetValue() : app;
                if (!appDef) continue;
                
                // Check if this is the target appearance
                var appName = appDef.Name ? appDef.Name.toString() : "";
                if (targetAppearance !== "default" && appName.toLowerCase() !== targetAppearance.toLowerCase()) {
                    continue;
                }
                
                // Extract from compiled data
                if (appDef.CompiledData && appDef.CompiledData.Data && appDef.CompiledData.Data.Chunks) {
                    var chunks = appDef.CompiledData.Data.Chunks;
                    for (var c = 0; c < chunks.length; c++) {
                        extractPathsFromChunk(chunks[c], result);
                    }
                }
                
                // If we found the target appearance, stop searching
                if (targetAppearance !== "default") {
                    break;
                }
            }
        }
    } catch (ex) {
        logger.Warning("Error analyzing appearance: " + ex.message);
    }
    
    return result;
}

function extractPathsFromChunk(chunk, result) {
    if (!chunk) return;
    
    try {
        // Check for mesh reference
        if (chunk.Mesh && chunk.Mesh.DepotPath) {
            var meshPath = chunk.Mesh.DepotPath.toString();
            if (meshPath && meshPath.length > 0 && meshPath.endsWith(".mesh") && result.meshPaths.indexOf(meshPath) === -1) {
                result.meshPaths.push(meshPath);
            }
        }
        
        // Check for rig reference
        if (chunk.Rig && chunk.Rig.DepotPath) {
            var rigPath = chunk.Rig.DepotPath.toString();
            if (rigPath && rigPath.length > 0 && result.rigPaths && result.rigPaths.indexOf(rigPath) === -1) {
                result.rigPaths.push(rigPath);
            }
        }
        
        // Check for baseMesh (morphtargets)
        if (chunk.BaseMesh && chunk.BaseMesh.DepotPath) {
            var baseMeshPath = chunk.BaseMesh.DepotPath.toString();
            if (baseMeshPath && baseMeshPath.length > 0 && result.meshPaths.indexOf(baseMeshPath) === -1) {
                result.meshPaths.push(baseMeshPath);
            }
        }
        
        // Check for appearance resource in component
        if (chunk.AppearanceResource && chunk.AppearanceResource.DepotPath) {
            var appResPath = chunk.AppearanceResource.DepotPath.toString();
            if (appResPath && appResPath.length > 0 && result.appearanceFiles && result.appearanceFiles.indexOf(appResPath) === -1) {
                result.appearanceFiles.push(appResPath);
            }
        }
        
        // Recursively check nested structures using Object.keys for better performance
        var keys;
        try {
            keys = Object.keys(chunk);
        } catch (keysEx) {
            // Some .NET objects may not support Object.keys, skip recursive check
            return;
        }
        
        for (var ki = 0; ki < keys.length; ki++) {
            var key = keys[ki];
            var value = chunk[key];
            if (value && typeof value === 'object') {
                if (Array.isArray(value)) {
                    for (var i = 0; i < value.length; i++) {
                        if (value[i] && typeof value[i] === 'object') {
                            extractPathsFromChunk(value[i], result);
                        }
                    }
                } else {
                    extractPathsFromChunk(value, result);
                }
            }
        }
    } catch (ex) {
        // Log errors in recursive extraction for debugging purposes
        // These are expected when accessing certain .NET object properties
    }
}
