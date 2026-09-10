/**
 * LocationMap Component
 * ---------------------
 * Interactive map component featuring automatic centering, live marker movement,
 * and dynamic layer switching between Satellite imagery and Street/Topo map.
 * 
 * Key fixes and capabilities:
 * 1. Fixed height: 450px explicitly declared on both the wrapper and MapContainer.
 * 2. Auto-resizing: Calls map.invalidateSize() on mount and layer toggle to ensure
 *    tiles never fail to render.
 * 3. Satellite and Street layers:
 *    - Street: OpenStreetMap standard tiles
 *    - Satellite: Esri World Imagery high-resolution satellite tiles
 *    - Prepared for dynamic Google Earth Engine raster tiles via `geeTileUrl` prop.
 * 4. Automatic Marker Movement:
 *    Marker updates immediately as latitude and longitude change, with smooth `flyTo` animation.
 * 5. Full Zoom Controls (+ / -) enabled.
 * 6. Legend and Coordinates Pill placed inside the map card container.
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

// Custom high-contrast red map pin SVG icon matching Reference Image 2 & 3
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
 * 1. Automatic flyTo when latitude or longitude changes.
 * 2. InvalidateSize on mount to ensure tiles are immediately visible.
 * 3. Bidirectional layer change listening from Leaflet LayersControl.
 */
const MapViewController = ({ targetLocation, zoomLevel = 9, activeLayer, onLayerChange }) => {
  const map = useMap();

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

  // Smooth camera flyTo when coordinates change
  useEffect(() => {
    if (
      targetLocation &&
      typeof targetLocation.latitude === 'number' &&
      typeof targetLocation.longitude === 'number' &&
      !isNaN(targetLocation.latitude) &&
      !isNaN(targetLocation.longitude)
    ) {
      map.flyTo([targetLocation.latitude, targetLocation.longitude], zoomLevel, {
        animate: true,
        duration: 1.2,
      });
    }
  }, [targetLocation?.latitude, targetLocation?.longitude, zoomLevel, map]);

  return null;
};

const LocationMap = ({ selectedLocation, geeTileUrl = null }) => {
  // Layer mode: 'street' (default) or 'satellite'
  const [activeLayer, setActiveLayer] = useState('street');

  // Fallback default coordinates if none provided
  const currentLocation = selectedLocation || { latitude: 18.5234, longitude: 79.1234 };

  const hasValidLocation =
    typeof currentLocation.latitude === 'number' &&
    typeof currentLocation.longitude === 'number' &&
    !isNaN(currentLocation.latitude) &&
    !isNaN(currentLocation.longitude);

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
      {/* Map Header with Layer Toggle and Active Coordinate Pill matching Reference Image 3 */}
      <div className="map-card-header">
        <div className="map-title-group">
          <svg className="map-header-icon" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z" />
          </svg>
          <h2 id="map-heading" className="card-title">
            Automatic Location Map & Layer Viewer
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

          {/* Real-time Coordinate Display Pill */}
          {hasValidLocation && (
            <div className="header-coords-pill" title="Current Coordinates">
              <svg className="pill-radio-icon" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/>
              </svg>
              <span>
                {currentLocation.latitude}°, {currentLocation.longitude}°
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Interactive Map Viewport with explicit 450px height */}
      <div className="map-container-wrapper" style={{ height: '450px', width: '100%' }}>
        <MapContainer
          center={[currentLocation.latitude, currentLocation.longitude]}
          zoom={9}
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

          {/* Automatic camera re-centering controller & layer synchronization */}
          <MapViewController
            targetLocation={currentLocation}
            zoomLevel={9}
            activeLayer={activeLayer}
            onLayerChange={setActiveLayer}
          />

          {/* Interactive Marker at Target Coordinates */}
          {hasValidLocation && (
            <Marker
              position={[currentLocation.latitude, currentLocation.longitude]}
              icon={customPin}
            >
              <Popup>
                <div className="map-popup-content">
                  <strong>Selected Target</strong>
                  <p>Lat: {currentLocation.latitude}°</p>
                  <p>Lon: {currentLocation.longitude}°</p>
                </div>
              </Popup>
            </Marker>
          )}
        </MapContainer>

        {/* Bottom Banner Matching Reference Concept */}
        <div className="map-reposition-banner">
          <span className="banner-pulse-dot"></span>
          <span>Target marker updates automatically as coordinates change</span>
        </div>

        {/* Map Legend Overlay matching Reference Image 2 */}
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
    </section>
  );
};

export default LocationMap;
