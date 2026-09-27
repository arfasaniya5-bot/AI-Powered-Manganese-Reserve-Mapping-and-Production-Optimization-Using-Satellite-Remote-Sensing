/**
 * LocationMap Component
 * ---------------------
 * Interactive geospatial map component featuring:
 * 1. Full mouse click-and-drag and touchscreen/finger pan.
 * 2. requestAnimationFrame-throttled real-time center coordinate readout during 'move' events.
 * 3. Fixed center crosshair reticle showing the exact target coordinates at the center.
 * 4. Click/tap location selection with smooth pan and onLocationSelect invocation.
 * 5. Drag-release ('moveend') callback for settled coordinate synchronization and reverse geocoding.
 * 6. Dual-layer switcher between Satellite imagery and Street/Topo map.
 * 7. Overlays matching reference mockup: top hint pill, floating bottom-center card, bottom-left legend, guidance bar.
 */

import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap, LayersControl } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Fix default Leaflet marker icon asset paths in bundlers (Vite/Webpack)
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

// Custom high-contrast red map pin SVG icon matching Reference Image
const createCustomPinIcon = () => {
  const pinSvg = `
    <svg width="34" height="42" viewBox="0 0 34 42" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M17 0C7.61 0 0 7.61 0 17C0 29.75 17 42 17 42C17 42 34 29.75 34 17C34 7.61 26.39 0 17 0Z" fill="#E53E3E"/>
      <circle cx="17" cy="17" r="6" fill="#FFFFFF"/>
    </svg>
  `;
  return L.divIcon({
    className: 'custom-map-marker',
    html: pinSvg,
    iconSize: [34, 42],
    iconAnchor: [17, 42],
    popupAnchor: [0, -42],
  });
};

const customPin = createCustomPinIcon();

/**
 * Controller child component that handles:
 * 1. Smooth flyTo when latitude or longitude changes (with threshold check).
 * 2. InvalidateSize on mount and layer change to ensure tiles are immediately visible.
 * 3. Bidirectional layer change listening from Leaflet LayersControl.
 * 4. Explicit dragging & touch interaction enablement.
 * 5. requestAnimationFrame-throttled center coordinate updates during mouse/touch drag ('move', 'drag').
 * 6. Settled coordinate emission on 'moveend'.
 * 7. Click-to-select map handler with smooth pan and onLocationSelect invocation.
 */
const MapViewController = ({
  targetLocation,
  zoomLevel = 9,
  activeLayer,
  onLayerChange,
  onCenterChange,
  onDragEnd,
  onLocationSelect,
}) => {
  const map = useMap();

  // Ensure map dragging and touch controls are fully active
  useEffect(() => {
    if (!map) return;
    if (map.dragging && !map.dragging.enabled()) {
      map.dragging.enable();
    }
    if (map.touchZoom && !map.touchZoom.enabled()) {
      map.touchZoom.enable();
    }
    if (map.doubleClickZoom && !map.doubleClickZoom.enabled()) {
      map.doubleClickZoom.enable();
    }
    if (map.scrollWheelZoom && !map.scrollWheelZoom.enabled()) {
      map.scrollWheelZoom.enable();
    }
  }, [map]);

  // Invalidate map size to prevent gray/empty tile issues
  useEffect(() => {
    const timer = setTimeout(() => {
      map.invalidateSize();
    }, 150);
    return () => clearTimeout(timer);
  }, [map, activeLayer]);

  // Listen to Leaflet native LayersControl switch events
  useEffect(() => {
    const handleBaseLayerChange = (e) => {
      if (e.name && e.name.toLowerCase().includes('satellite')) {
        onLayerChange('satellite');
      } else {
        onLayerChange('street');
      }
    };
    map.on('baselayerchange', handleBaseLayerChange);
    return () => {
      map.off('baselayerchange', handleBaseLayerChange);
    };
  }, [map, onLayerChange]);

  // Continuously track center coordinates during mouse/touch drag with requestAnimationFrame throttling
  useEffect(() => {
    if (!map || !onCenterChange) return;

    let rafId = null;

    const handleCenterUpdate = () => {
      if (rafId) return;
      rafId = requestAnimationFrame(() => {
        rafId = null;
        const center = map.getCenter();
        if (center && typeof center.lat === 'number' && typeof center.lng === 'number') {
          onCenterChange({
            latitude: Number(center.lat.toFixed(4)),
            longitude: Number(center.lng.toFixed(4)),
          });
        }
      });
    };

    map.on('move', handleCenterUpdate);
    map.on('drag', handleCenterUpdate);

    // On drag release / moveend: cancel pending RAF, emit final settled coordinates
    const handleMoveEnd = () => {
      if (rafId) {
        cancelAnimationFrame(rafId);
        rafId = null;
      }
      const center = map.getCenter();
      if (center && typeof center.lat === 'number' && typeof center.lng === 'number') {
        const cleanLat = Number(center.lat.toFixed(4));
        const cleanLon = Number(center.lng.toFixed(4));
        onCenterChange({
          latitude: cleanLat,
          longitude: cleanLon,
        });
        if (onDragEnd) {
          onDragEnd(cleanLat, cleanLon);
        }
      }
    };

    map.on('moveend', handleMoveEnd);

    // Initial center update
    handleCenterUpdate();

    return () => {
      if (rafId) cancelAnimationFrame(rafId);
      map.off('move', handleCenterUpdate);
      map.off('drag', handleCenterUpdate);
      map.off('moveend', handleMoveEnd);
    };
  }, [map, onCenterChange, onDragEnd]);

  // Map click handler: panTo clicked point without snapping, and trigger location selection
  useEffect(() => {
    if (!map || !onLocationSelect) return;

    const handleMapClick = (e) => {
      if (!e.latlng) return;
      const cleanLat = Number(e.latlng.lat.toFixed(4));
      const cleanLon = Number(e.latlng.lng.toFixed(4));

      // Smoothly pan camera to clicked point
      map.panTo([cleanLat, cleanLon], { animate: true, duration: 0.5 });

      // Notify parent to update marker, form inputs, reverse geocoding, and trigger prediction
      onLocationSelect(cleanLat, cleanLon);
    };

    map.on('click', handleMapClick);
    return () => {
      map.off('click', handleMapClick);
    };
  }, [map, onLocationSelect]);

  // Smooth camera flyTo when coordinates change externally (e.g. typed in form or clicked in preset)
  useEffect(() => {
    if (
      targetLocation &&
      typeof targetLocation.latitude === 'number' &&
      typeof targetLocation.longitude === 'number' &&
      !isNaN(targetLocation.latitude) &&
      !isNaN(targetLocation.longitude)
    ) {
      const currentCenter = map.getCenter();
      const latDiff = Math.abs(currentCenter.lat - targetLocation.latitude);
      const lonDiff = Math.abs(currentCenter.lng - targetLocation.longitude);

      // Only flyTo if the change is significant (> 0.0005 deg)
      // If within 0.0005 deg, panTo from map click already handled it smoothly
      if (latDiff > 0.0005 || lonDiff > 0.0005) {
        map.flyTo([targetLocation.latitude, targetLocation.longitude], zoomLevel, {
          animate: true,
          duration: 1.0,
        });
      }
    }
  }, [targetLocation?.latitude, targetLocation?.longitude, zoomLevel, map]);

  return null;
};

const LocationMap = ({
  selectedLocation,
  onLocationSelect = null,
  onDragEnd = null,
  geeTileUrl = null,
}) => {
  // Layer mode: 'street' (default) or 'satellite'
  const [activeLayer, setActiveLayer] = useState('street');

  // Fallback default coordinates if none provided
  const currentLocation = selectedLocation || { latitude: 18.5234, longitude: 79.1234 };

  const hasValidLocation =
    typeof currentLocation.latitude === 'number' &&
    typeof currentLocation.longitude === 'number' &&
    !isNaN(currentLocation.latitude) &&
    !isNaN(currentLocation.longitude);

  // Live map center coordinates (continuously updated while dragging map with mouse or finger)
  const [centerCoords, setCenterCoords] = useState({
    latitude: hasValidLocation ? currentLocation.latitude : 18.5234,
    longitude: hasValidLocation ? currentLocation.longitude : 79.1234,
  });

  // Keep centerCoords in sync if targetLocation changes externally
  useEffect(() => {
    if (hasValidLocation) {
      setCenterCoords({
        latitude: currentLocation.latitude,
        longitude: currentLocation.longitude,
      });
    }
  }, [currentLocation.latitude, currentLocation.longitude, hasValidLocation]);

  // Tile layer configurations
  const streetTileUrl = 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png';
  const streetAttribution =
    '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors';

  // Satellite tile layer: Uses dynamic GEE tile URL if provided, otherwise standard high-res satellite
  const satelliteTileUrl =
    geeTileUrl ||
    'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}';
  const satelliteAttribution =
    'Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and GIS User Community';

  return (
    <section className="card map-card" aria-labelledby="map-heading">
      {/* Map Header with Layer Toggle matching Reference Image */}
      <div className="map-card-header">
        <div className="map-title-group">
          <svg className="map-header-icon" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z" />
          </svg>
          <h2 id="map-heading" className="card-title">
            Interactive Location Map
          </h2>
        </div>

        <div className="map-header-controls">
          {/* Layer Switcher Buttons: Satellite & Street / Topo */}
          <div className="layer-switcher-group" role="group" aria-label="Map Layer Toggle">
            <button
              type="button"
              className={`layer-toggle-btn ${activeLayer === 'satellite' ? 'layer-btn-active' : ''}`}
              onClick={() => setActiveLayer('satellite')}
              title="Switch to Satellite imagery layer"
            >
              <svg className="layer-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="9" />
                <path d="M3.6 9h16.8M3.6 15h16.8M12 3a14 14 0 0 0 0 18M12 3a14 14 0 0 1 0 18" />
              </svg>
              <span>Satellite</span>
            </button>
            <button
              type="button"
              className={`layer-toggle-btn ${activeLayer === 'street' ? 'layer-btn-active' : ''}`}
              onClick={() => setActiveLayer('street')}
              title="Switch to Street / Topographic layer"
            >
              <svg className="layer-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polygon points="12 2 2 7 12 12 22 7 12 2" />
                <polyline points="2 17 12 22 22 17" />
                <polyline points="2 12 12 17 22 12" />
              </svg>
              <span>Street / Topo</span>
            </button>
          </div>
        </div>
      </div>

      {/* Interactive Map Viewport with explicit 450px height */}
      <div className="map-container-wrapper" style={{ height: '450px', width: '100%', position: 'relative' }}>
        <MapContainer
          center={[currentLocation.latitude, currentLocation.longitude]}
          zoom={9}
          dragging={true}
          touchZoom={true}
          doubleClickZoom={true}
          scrollWheelZoom={true}
          zoomControl={true}
          style={{ height: '450px', width: '100%', borderRadius: '8px' }}
          className="leaflet-map-canvas"
        >
          {/* Leaflet LayersControl: allows toggling between Street / Topographic and Satellite */}
          <LayersControl position="topright">
            <LayersControl.BaseLayer checked={activeLayer === 'street'} name="Street / Topographic">
              <TileLayer
                attribution={streetAttribution}
                url={streetTileUrl}
                maxZoom={19}
              />
            </LayersControl.BaseLayer>
            <LayersControl.BaseLayer checked={activeLayer === 'satellite'} name="Satellite">
              <TileLayer
                attribution={satelliteAttribution}
                url={satelliteTileUrl}
                maxZoom={19}
              />
            </LayersControl.BaseLayer>
          </LayersControl>

          {/* Automatic camera re-centering controller, dragging tracker, & layer synchronization */}
          <MapViewController
            targetLocation={currentLocation}
            zoomLevel={9}
            activeLayer={activeLayer}
            onLayerChange={setActiveLayer}
            onCenterChange={setCenterCoords}
            onDragEnd={onDragEnd}
            onLocationSelect={onLocationSelect}
          />

          {/* Interactive Marker at Selected Coordinates */}
          {hasValidLocation && (
            <Marker
              position={[currentLocation.latitude, currentLocation.longitude]}
              icon={customPin}
            >
              <Popup>
                <div className="map-popup-content">
                  <strong>Selected Target</strong>
                  <p>Lat: {currentLocation.latitude.toFixed(4)}°N</p>
                  <p>Lon: {currentLocation.longitude.toFixed(4)}°E</p>
                </div>
              </Popup>
            </Marker>
          )}
        </MapContainer>

        {/* Center Crosshair / Target Reticle Overlay (Fixed at 50% 50%, non-blocking) */}
        <div className="map-fixed-crosshair" aria-hidden="true" title="Map Center">
          <svg width="44" height="44" viewBox="0 0 44 44" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="22" cy="22" r="14" stroke="#ef4444" strokeWidth="2" fill="none" />
            <circle cx="22" cy="22" r="2.5" fill="#ef4444" />
            <line x1="22" y1="2" x2="22" y2="10" stroke="#ef4444" strokeWidth="2" strokeLinecap="round" />
            <line x1="22" y1="34" x2="22" y2="42" stroke="#ef4444" strokeWidth="2" strokeLinecap="round" />
            <line x1="2" y1="22" x2="10" y2="22" stroke="#ef4444" strokeWidth="2" strokeLinecap="round" />
            <line x1="34" y1="22" x2="42" y2="22" stroke="#ef4444" strokeWidth="2" strokeLinecap="round" />
          </svg>
        </div>

        {/* Top-Center Drag Hint Pill matching Reference Screenshot */}
        <div className="map-drag-hint-pill" aria-hidden="true">
          <div className="hint-icon-circle">
            <svg viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z"/>
            </svg>
          </div>
          <div className="hint-text-group">
            <span className="hint-line-primary">Drag the map with mouse or finger</span>
            <span className="hint-line-secondary">Coordinates update in real time</span>
          </div>
        </div>

        {/* Bottom-Center Floating Map Center Card matching Reference Screenshot */}
        <div className="map-center-coords-card" aria-live="polite" title="Map Center Coordinates">
          <div className="center-coords-text">
            {centerCoords.latitude.toFixed(4)}° N , {centerCoords.longitude.toFixed(4)}° E
          </div>
          <div className="center-coords-sublabel">(Map Center)</div>
        </div>

        {/* Map Legend Overlay matching Reference Image (Bottom-Left) */}
        <div className="map-legend-overlay">
          <div className="legend-item">
            <span className="legend-dot dot-high"></span>
            <span className="legend-text">High Potential</span>
          </div>
          <div className="legend-item">
            <span className="legend-dot dot-medium"></span>
            <span className="legend-text">Medium Potential</span>
          </div>
          <div className="legend-item">
            <span className="legend-dot dot-low"></span>
            <span className="legend-text">Low Potential</span>
          </div>
        </div>
      </div>

      {/* Sub-map Guidance Bar matching Reference Screenshot */}
      <div className="map-bottom-guidance-bar">
        <svg className="guidance-crosshair-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="12" cy="12" r="7" />
          <line x1="12" y1="2" x2="12" y2="6" />
          <line x1="12" y1="18" x2="12" y2="22" />
          <line x1="2" y1="12" x2="6" y2="12" />
          <line x1="18" y1="12" x2="22" y2="12" />
        </svg>
        <span>Move the map to explore different locations. Click on any location to get prediction.</span>
      </div>
    </section>
  );
};

export default LocationMap;
