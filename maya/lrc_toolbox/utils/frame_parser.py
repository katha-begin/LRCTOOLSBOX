# -*- coding: utf-8 -*-
"""
Frame Range Parser

Flexible frame range parsing with support for:
- Comma-separated frames: "1,5,10,20"
- Ranges: "10-20"
- Steps: "1-100x5" (always includes first and last)
- Combined: "1,10-20,50,60-70x2"
"""

from typing import List, Set, Tuple


def parse_frame_range(frame_string: str) -> List[int]:
    """
    Parse frame range string into list of frame numbers.
    
    Supported syntax:
    - Single frames: "1,5,10"
    - Ranges: "10-20" (inclusive)
    - Steps: "1-100x5" (every 5th frame, always includes first and last)
    - Combined: "1,10-20,50,60-70x2"
    
    Args:
        frame_string: Frame range string
        
    Returns:
        Sorted list of unique frame numbers
        
    Raises:
        ValueError: If frame string syntax is invalid
        
    Examples:
        >>> parse_frame_range("1,5,10")
        [1, 5, 10]
        
        >>> parse_frame_range("10-20")
        [10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]
        
        >>> parse_frame_range("1-10x3")
        [1, 4, 7, 10]  # Always includes first and last
        
        >>> parse_frame_range("1,10-20,50")
        [1, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 50]
    """
    if not frame_string or not frame_string.strip():
        raise ValueError("Frame range string cannot be empty")
    
    frames: Set[int] = set()
    
    # Split by comma
    parts = frame_string.split(',')
    
    for part in parts:
        part = part.strip()
        if not part:
            continue
        
        try:
            # Check for step syntax: "1-100x5"
            if 'x' in part:
                frames.update(_parse_step_range(part))
            
            # Check for range syntax: "10-20"
            elif '-' in part:
                frames.update(_parse_simple_range(part))
            
            # Single frame: "5"
            else:
                frame = int(part)
                if frame < 0:
                    raise ValueError(f"Negative frame numbers not supported: {frame}")
                frames.add(frame)
                
        except ValueError as e:
            raise ValueError(f"Invalid frame syntax in '{part}': {e}")
    
    if not frames:
        raise ValueError("No valid frames found in frame range string")
    
    return sorted(list(frames))


def _parse_simple_range(range_str: str) -> Set[int]:
    """
    Parse simple range like "10-20".
    
    Args:
        range_str: Range string (e.g., "10-20")
        
    Returns:
        Set of frame numbers in range
    """
    parts = range_str.split('-')
    
    if len(parts) != 2:
        raise ValueError(f"Invalid range format: {range_str}")
    
    start = int(parts[0].strip())
    end = int(parts[1].strip())
    
    if start < 0 or end < 0:
        raise ValueError("Negative frame numbers not supported")
    
    if start > end:
        raise ValueError(f"Start frame ({start}) must be <= end frame ({end})")
    
    return set(range(start, end + 1))


def _parse_step_range(step_str: str) -> Set[int]:
    """
    Parse step range like "1-100x5".
    
    Always includes first and last frames.
    
    Args:
        step_str: Step range string (e.g., "1-100x5")
        
    Returns:
        Set of frame numbers with step
    """
    # Split by 'x' to get range and step
    parts = step_str.split('x')
    
    if len(parts) != 2:
        raise ValueError(f"Invalid step format: {step_str}")
    
    range_part = parts[0].strip()
    step = int(parts[1].strip())
    
    if step <= 0:
        raise ValueError(f"Step must be positive: {step}")
    
    # Parse the range part
    range_parts = range_part.split('-')
    
    if len(range_parts) != 2:
        raise ValueError(f"Invalid range in step: {range_part}")
    
    start = int(range_parts[0].strip())
    end = int(range_parts[1].strip())
    
    if start < 0 or end < 0:
        raise ValueError("Negative frame numbers not supported")
    
    if start > end:
        raise ValueError(f"Start frame ({start}) must be <= end frame ({end})")
    
    frames: Set[int] = set()
    
    # Always include first frame
    frames.add(start)
    
    # Add stepped frames
    current = start
    while current <= end:
        frames.add(current)
        current += step
    
    # Always include last frame
    frames.add(end)
    
    return frames


def validate_frame_range(frame_string: str) -> Tuple[bool, str]:
    """
    Validate frame range string syntax.
    
    Args:
        frame_string: Frame range string to validate
        
    Returns:
        Tuple of (is_valid, error_message)
        If valid, error_message is empty string
    """
    try:
        parse_frame_range(frame_string)
        return True, ""
    except ValueError as e:
        return False, str(e)


def get_frame_count(frame_string: str) -> int:
    """
    Get number of frames in frame range.
    
    Args:
        frame_string: Frame range string
        
    Returns:
        Number of frames
    """
    try:
        frames = parse_frame_range(frame_string)
        return len(frames)
    except ValueError:
        return 0


def format_frame_range(frames: List[int]) -> str:
    """
    Format list of frames into compact range string.
    
    Args:
        frames: List of frame numbers
        
    Returns:
        Formatted frame range string
        
    Examples:
        >>> format_frame_range([1, 2, 3, 4, 5])
        "1-5"
        
        >>> format_frame_range([1, 5, 10, 15])
        "1,5,10,15"
        
        >>> format_frame_range([1, 2, 3, 10, 11, 12])
        "1-3,10-12"
    """
    if not frames:
        return ""
    
    sorted_frames = sorted(frames)
    ranges = []
    
    start = sorted_frames[0]
    end = start
    
    for i in range(1, len(sorted_frames)):
        if sorted_frames[i] == end + 1:
            # Continue range
            end = sorted_frames[i]
        else:
            # End current range, start new one
            if start == end:
                ranges.append(str(start))
            else:
                ranges.append(f"{start}-{end}")
            
            start = sorted_frames[i]
            end = start
    
    # Add final range
    if start == end:
        ranges.append(str(start))
    else:
        ranges.append(f"{start}-{end}")
    
    return ",".join(ranges)


def get_first_last_frames(frame_string: str) -> Tuple[int, int]:
    """
    Get first and last frame numbers from frame range.
    
    Args:
        frame_string: Frame range string
        
    Returns:
        Tuple of (first_frame, last_frame)
    """
    frames = parse_frame_range(frame_string)
    return frames[0], frames[-1]

