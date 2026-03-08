package com.secemumod.demo.controller;

import com.secemumod.demo.dto.ApiResponse;
import com.secemumod.demo.dto.LoginRequest;
import com.secemumod.demo.service.MvpService;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

/**
 * POST /api/v1/auth/login
 * Body: { "username": "...", "password": "..." }
 * Response: { "data": { "token": "JWT" } }
 */
@RestController
@RequestMapping("/api/v1/auth")
public class AuthController {

    private final MvpService mvpService;

    public AuthController(MvpService mvpService) {
        this.mvpService = mvpService;
    }

    @PostMapping("/login")
    public ApiResponse<Map<String, String>> login(@RequestBody LoginRequest req) {
        String token = mvpService.login(req.getUsername(), req.getPassword());
        if (token == null) {
            return ApiResponse.fail(401, "Invalid username or password");
        }
        return ApiResponse.ok(Map.of("token", token));
    }
}
