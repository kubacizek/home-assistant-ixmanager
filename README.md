# iXmanager Integration (Experimental)

[!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://buymeacoffee.com/kubacizek)
[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/hacs/integration)

This integration provides support for the [R-EVC Wallbox EcoVolter](https://r-evc.com/index.php?route=product/product&path=60&product_id=135), utilizing the iXmanager [API](https://evcharger.ixcommand.com).

## Features
- Seamless integration with the R-EVC Wallbox EcoVolter charger.
- Control and monitor your wallbox through Home Assistant.
- Easy setup and configuration with iXmanager API.

## Prerequisites
Before setting up this integration, ensure you have:
- Connected your wallbox with the iXmanager app on iOS or Android.
- Generated an API key from your [iXmanager account](https://www.ixfield.com/app/account).

## Installation

### HACS Installation (Recommended)
1. Ensure that [HACS](https://hacs.xyz) is installed in your Home Assistant instance.
2. Add this integration via HACS

### Manual Installation
1. Download and extract the integration files to the `custom_components` directory in your Home Assistant configuration folder.
2. Restart Home Assistant to load the integration.

## Configuration

1. Open Home Assistant and navigate to `Configuration > Devices & Services`.
2. Click on `Add Integration` and search for "iXmanager".
3. Enter the serial number of your wallbox (found on the charger or in your [iXmanager account](https://www.ixfield.com/app/account)) and your API key.
4. Complete the setup wizard to finalize the integration.

## Usage
Once the integration is configured, you can start using your R-EVC Wallbox EcoVolter directly from Home Assistant. Monitor charging status, control charging sessions, and integrate with other Home Assistant automations.