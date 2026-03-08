package com.secemumod.demo.controller;

import com.secemumod.demo.dto.ApiResponse;
import com.secemumod.demo.dto.BatchLaunchRequest;
import com.secemumod.demo.service.MvpService;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

/**
 * POST /api/v1/mod/batch-launch-secure  — get encryptedDek + downloadUrl
 * GET  /api/v1/mod/{modId}/download/{fileName} — download .aimg1 binary
 */
@RestController
@RequestMapping("/api/v1/mod")
public class ModController {

    private final MvpService mvpService;

    public ModController(MvpService mvpService) {
        this.mvpService = mvpService;
    }

    @PostMapping("/batch-launch-secure")
    public ApiResponse<Map<String, Object>> batchLaunchSecure(
            @RequestBody BatchLaunchRequest req,
            @RequestHeader("Authorization") String authHeader) {
        String token = extractToken(authHeader);
        if (token == null) {
            return ApiResponse.fail(401, "Missing or invalid Authorization header");
        }
        try {
            Map<String, Object> data = mvpService.batchLaunchSecure(req.getSelectedModIds(), token);
            return ApiResponse.ok(data);
        } catch (SecurityException e) {
            return ApiResponse.fail(401, e.getMessage());
        } catch (Exception e) {
            return ApiResponse.fail(500, "Internal error: " + e.getMessage());
        }
    }

    @GetMapping("/{modId}/download/{fileName}")
    public ResponseEntity<byte[]> downloadFile(
            @PathVariable Long modId,
            @PathVariable String fileName,
            @RequestHeader("Authorization") String authHeader) {
        String token = extractToken(authHeader);
        if (token == null) {
            return ResponseEntity.status(401).build();
        }
        try {
            byte[] data = mvpService.downloadFile(modId, fileName, token);
            return ResponseEntity.ok()
                    .header(HttpHeaders.CONTENT_DISPOSITION, "attachment; filename=\"" + fileName + "\"")
                    .contentType(MediaType.APPLICATION_OCTET_STREAM)
                    .body(data);
        } catch (SecurityException e) {
            return ResponseEntity.status(401).build();
        } catch (IllegalArgumentException e) {
            return ResponseEntity.status(404).build();
        } catch (Exception e) {
            return ResponseEntity.status(500).build();
        }
    }

    private String extractToken(String authHeader) {
        if (authHeader != null && authHeader.startsWith("Bearer ")) {
            return authHeader.substring(7);
        }
        return null;
    }
}
