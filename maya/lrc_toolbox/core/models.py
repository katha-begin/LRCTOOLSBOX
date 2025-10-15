"""
Core Data Models

This module defines the core data structures and schemas used throughout
the LRC Toolbox application for enhanced template management.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class ProjectType(Enum):
    """Project type enumeration."""
    SHOT = "shot"
    ASSET = "asset"


class TemplateType(Enum):
    """Template type enumeration."""
    MASTER = "master"
    KEY = "key"
    MICRO = "micro"
    CUSTOM = "custom"


class RenderLayerElement(Enum):
    """Render layer element enumeration."""
    BG = "BG"
    CHAR = "CHAR"
    ATMOS = "ATMOS"
    FX = "FX"


class RenderLayerVariance(Enum):
    """Render layer variance enumeration."""
    A = "A"
    B = "B"
    C = "C"


@dataclass
class ProjectInfo:
    """Project information data structure."""
    name: str
    root_path: str
    type: ProjectType
    created_date: datetime = field(default_factory=datetime.now)
    last_modified: datetime = field(default_factory=datetime.now)
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class VersionInfo:
    """Version information data structure."""
    version_number: int
    file_path: str
    file_name: str
    file_size: int
    created_date: datetime
    created_by: str
    is_hero: bool = False
    is_published: bool = False
    comment: str = ""
    checksum: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TemplateInfo:
    """Template information data structure for enhanced template management."""
    name: str
    template_type: TemplateType
    context_path: str
    package_path: str
    version: str = "v001"
    created_date: datetime = field(default_factory=datetime.now)
    created_by: str = ""
    description: str = ""
    maya_version: str = ""
    renderer: str = ""
    
    # Template hierarchy and inheritance
    parent_template: Optional[str] = None
    inherited_from: List[str] = field(default_factory=list)
    required_assets: List[str] = field(default_factory=list)
    
    # Package contents
    maya_light_file: Optional[str] = None
    render_layers_file: Optional[str] = None
    render_settings_file: Optional[str] = None
    aovs_file: Optional[str] = None
    package_info_file: Optional[str] = None
    
    # Statistics
    light_count: int = 0
    light_types: List[str] = field(default_factory=list)
    layer_count: int = 0
    layer_names: List[str] = field(default_factory=list)
    
    # Metadata
    checksum: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FileInfo:
    """File information data structure."""
    name: str
    path: str
    size: int
    modified_date: datetime
    file_type: str
    is_directory: bool = False
    version_info: Optional[VersionInfo] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class NavigationContext:
    """Navigation context data structure."""
    type: ProjectType
    
    # Shot context
    episode: str = ""
    sequence: str = ""
    shot: str = ""
    
    # Asset context
    category: str = ""
    subcategory: str = ""
    asset: str = ""
    
    # Common
    department: str = ""
    
    # Computed properties
    @property
    def is_valid_shot_context(self) -> bool:
        """Check if shot context is valid."""
        return (self.type == ProjectType.SHOT and 
                all([self.episode, self.sequence, self.shot, self.department]))
    
    @property
    def is_valid_asset_context(self) -> bool:
        """Check if asset context is valid."""
        return (self.type == ProjectType.ASSET and 
                all([self.category, self.subcategory, self.asset, self.department]))
    
    @property
    def context_path(self) -> str:
        """Get the context path string."""
        if self.type == ProjectType.SHOT:
            return f"{self.episode}/{self.sequence}/{self.shot}/{self.department}"
        else:
            return f"{self.category}/{self.subcategory}/{self.asset}/{self.department}"
    
    @property
    def context_prefix(self) -> str:
        """Get the context prefix for naming conventions."""
        if self.type == ProjectType.SHOT:
            return self.shot
        else:
            return self.asset.upper()

    def get_display_name(self) -> str:
        """Get display name for the navigation context."""
        if self.type == ProjectType.SHOT:
            if self.is_valid_shot_context:
                return f"🎬 {self.episode}/{self.sequence}/{self.shot}/{self.department}"
            else:
                parts = [p for p in [self.episode, self.sequence, self.shot, self.department] if p]
                return f"🎬 {'/'.join(parts)}" if parts else "🎬 Shot Navigation"
        else:
            if self.is_valid_asset_context:
                return f"🎨 {self.category}/{self.subcategory}/{self.asset}/{self.department}"
            else:
                parts = [p for p in [self.category, self.subcategory, self.asset, self.department] if p]
                return f"🎨 {'/'.join(parts)}" if parts else "🎨 Asset Navigation"


@dataclass
class RenderLayerInfo:
    """Render layer information data structure."""
    name: str
    prefix: str
    element: RenderLayerElement
    variance: Optional[RenderLayerVariance] = None
    created_date: datetime = field(default_factory=datetime.now)
    is_active: bool = True
    collections: List[str] = field(default_factory=list)
    overrides: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def full_name(self) -> str:
        """Get the full render layer name following naming convention."""
        if self.element == RenderLayerElement.ATMOS:
            return f"{self.prefix}_{self.element.value}"
        else:
            variance_str = self.variance.value if self.variance else "A"
            return f"{self.prefix}_{self.element.value}_{variance_str}"


@dataclass
class LightInfo:
    """Light information data structure."""
    name: str
    light_type: str
    hierarchy_level: str  # Master, Key, Child
    index: int
    created_date: datetime = field(default_factory=datetime.now)
    is_selected: bool = False
    group_name: Optional[str] = None
    transform_data: Dict[str, Any] = field(default_factory=dict)
    attribute_data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def formatted_name(self) -> str:
        """Get the formatted light name following naming convention."""
        index_str = f"{self.index:03d}"
        
        if self.hierarchy_level == "Master":
            return f"MASTER_{self.light_type}_{index_str}"
        elif self.hierarchy_level == "Key":
            # This would be populated from context
            prefix = "SH0010"  # Placeholder
            return f"{prefix}_{self.light_type}_{index_str}"
        else:  # Child
            prefix = "SH0010"  # Placeholder
            sub_type = "RIM"  # Placeholder
            return f"{prefix}_{self.light_type}_{sub_type}_{index_str}"


@dataclass
class ImportOptions:
    """Import options data structure."""
    import_mode: str = "additive"  # "replace" or "additive"
    check_existing_lights: bool = True
    rename_conflicts: bool = True
    preserve_layers: bool = True
    create_backup: bool = True
    selected_components: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExportOptions:
    """Export options data structure."""
    package_name: str
    package_type: TemplateType
    export_location: str
    selected_components: List[str] = field(default_factory=list)
    parent_template: Optional[str] = None
    description: str = ""
    include_dependencies: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


# Type aliases for better code readability
TemplatePackageList = List[TemplateInfo]
FileList = List[FileInfo]
LightList = List[LightInfo]
RenderLayerList = List[RenderLayerInfo]


# ============================================================================
# Batch Render Data Models
# ============================================================================

class RenderMethod(Enum):
    """Render execution method enumeration."""
    AUTO = "auto"  # Automatic with fallback
    MAYAPY_CUSTOM = "mayapy_custom"  # Priority 1: mayapy with custom script
    RENDER_EXE = "render_exe"  # Priority 2: Maya Render.exe
    MAYAPY_BASIC = "mayapy_basic"  # Priority 3: Basic mayapy render


class ProcessStatus(Enum):
    """Render process status enumeration."""
    WAITING = "waiting"
    INITIALIZING = "initializing"
    RENDERING = "rendering"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class RenderMode(Enum):
    """Render mode enumeration."""
    SEPARATE = "separate"  # Render each layer separately
    COMBINED = "combined"  # Render all layers together


@dataclass
class GPUInfo:
    """GPU information data structure."""
    device_id: int
    name: str
    memory_total: int  # In bytes
    memory_free: int  # In bytes
    is_available: bool
    compute_capability: Optional[str] = None


@dataclass
class SystemInfo:
    """System information data structure."""
    gpu_count: int
    gpus: List[GPUInfo] = field(default_factory=list)
    cpu_cores: int = 0
    cpu_threads: int = 0
    available_gpus: int = 0
    available_cpu_threads: int = 0
    reserved_gpu_count: int = 1
    reserved_cpu_threads: int = 4


@dataclass
class RenderConfig:
    """Render configuration data structure."""
    scene_file: str
    layers: List[str]
    frame_range: str
    gpu_id: int = 1
    cpu_threads: int = 4
    render_mode: RenderMode = RenderMode.SEPARATE
    render_method: RenderMethod = RenderMethod.AUTO
    renderer: str = "redshift"
    output_path: Optional[str] = None
    custom_settings: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RenderProcess:
    """Render process data structure."""
    process_id: str
    layer_name: str
    frame_range: str
    frames: List[int] = field(default_factory=list)
    status: ProcessStatus = ProcessStatus.WAITING
    progress: float = 0.0
    current_frame: int = 0
    total_frames: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    temp_file_path: Optional[str] = None
    render_method: RenderMethod = RenderMethod.AUTO
    error_message: Optional[str] = None
    log_messages: List[str] = field(default_factory=list)
    output_path: Optional[str] = None  # Parsed from render logs
